import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Any
import re
import io
import unicodedata

def validate_excel_bytes(file_bytes: bytes) -> None:
    if not file_bytes or len(file_bytes) < 8:
        raise ValueError("O arquivo enviado está vazio ou corrompido (tamanho insuficiente).")
    
    is_zip = file_bytes.startswith(b'PK\x03\x04') or file_bytes.startswith(b'PK\x05\x06')
    is_ole = file_bytes.startswith(b'\xd0\xcf\x11\xe0')

    if not (is_zip or is_ole):
        raise ValueError("Formato de arquivo inválido. O arquivo não possui uma estrutura Excel (.xlsx ou .xls) válida.")

def normalize_str(s: Any) -> str:
    if pd.isna(s) or s is None:
        return ""
    nfkd = unicodedata.normalize('NFKD', str(s))
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).upper().strip()

def clean_numeric(val: Any, abs_val: bool = False) -> Any:
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, (int, float, np.number)):
        if np.isnan(val) or np.isinf(val):
            return None
        res = float(val)
        return abs(res) if abs_val else res
    
    val_str = str(val).strip()
    if not val_str or any(err in val_str.lower() for err in ['total', 'soma', 'nan', 'none', '-', 'check', '#ref!', '#value!', '#n/a', '#null!', '#div/0!', '#name?']):
        return None
    
    val_str = re.sub(r'[R\$\s%]', '', val_str)
    
    if '.' in val_str and ',' in val_str:
        val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str:
        val_str = val_str.replace(',', '.')
        
    try:
        res = float(val_str)
        return abs(res) if abs_val else res
    except ValueError:
        return None

def parse_date(val: Any) -> date | None:
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.date()
    if isinstance(val, date):
        return val
    
    if isinstance(val, (int, float)) and not np.isnan(val):
        try:
            if 30000 <= val <= 70000:
                dt = pd.to_datetime(val, unit='D', origin='1899-12-30')
                return dt.date()
        except Exception:
            pass

    val_str = str(val).strip()
    if not val_str or any(err in val_str.lower() for err in ['total', 'soma', 'nan', 'check', '#ref!', '#value!', '#n/a']):
        return None

    formats = ['%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d', '%m/%Y', '%m/%y', '%Y/%m', '%d-%m-%Y', '%Y-%m-%d %H:%M:%S']
    for fmt in formats:
        try:
            dt = datetime.strptime(val_str, fmt)
            return dt.date()
        except ValueError:
            pass
            
    try:
        dt = pd.to_datetime(val_str, errors='coerce')
        if not pd.isna(dt):
            return dt.date()
    except Exception:
        pass

    return None

def find_header_row(df_raw: pd.DataFrame, keywords: List[str]) -> int:
    for idx, row in df_raw.iterrows():
        row_cells = [normalize_str(x) for x in row.values if pd.notna(x)]
        matches = sum(1 for kw in keywords if any(kw in cell for cell in row_cells))
        if matches >= 2 or (len(keywords) == 1 and matches == 1):
            return idx
    return 0

class ExcelParserService:
    @staticmethod
    def parse_excel(file_bytes: bytes | io.BytesIO) -> Dict[str, Any]:
        warnings: List[str] = []

        if isinstance(file_bytes, bytes):
            validate_excel_bytes(file_bytes)
            file_bytes = io.BytesIO(file_bytes)
        elif isinstance(file_bytes, io.BytesIO):
            file_bytes.seek(0)
            raw = file_bytes.read()
            validate_excel_bytes(raw)
            file_bytes.seek(0)

        try:
            excel_file = pd.ExcelFile(file_bytes)
        except Exception as e:
            raise ValueError(f"Não foi possível abrir o arquivo como Excel: {str(e)}")

        parsed_data: Dict[str, Any] = {}
        sheet_names = excel_file.sheet_names

        debt_sheet = next((s for s in sheet_names if 'Planilhão' in s or '1|' in s or 'Debt' in s), None)
        if debt_sheet:
            parsed_data['debt_control'] = ExcelParserService._parse_debt_control(excel_file, debt_sheet)
        else:
            parsed_data['debt_control'] = []
            warnings.append("Aba de Controle de Dívida (Planilhão / Debt) não foi encontrada.")
            
        inv_sheet = next((s for s in sheet_names if 'Investimentos' in s or '2|' in s or 'Investment' in s), None)
        if inv_sheet:
            parsed_data['financial_investment'] = ExcelParserService._parse_financial_investment(excel_file, inv_sheet)
        else:
            parsed_data['financial_investment'] = []
            warnings.append("Aba de Investimentos Financeiros não foi encontrada.")

        re_sheet = next((s for s in sheet_names if 'Imóveis' in s or 'Imoveis' in s or '3|' in s), None)
        if re_sheet:
            parsed_data['real_estate'] = ExcelParserService._parse_real_estate(excel_file, re_sheet)
        else:
            parsed_data['real_estate'] = []
            warnings.append("Aba de Imóveis não foi encontrada.")

        live_sheet = next((s for s in sheet_names if any(k in normalize_str(s) for k in ['GADO', '4|', 'LIVESTOCK', 'REBANHO'])), None)
        livestock_summary = None
        if live_sheet:
            live_records, livestock_summary = ExcelParserService._parse_livestock(excel_file, live_sheet)
            parsed_data['livestock_inventory'] = live_records
        else:
            parsed_data['livestock_inventory'] = []
            warnings.append("Aba de Gado/Estoque Pecuário não foi encontrada.")

        veh_sheet = next((s for s in sheet_names if 'Bens Móveis' in s or 'Bens Moveis' in s or '5|' in s or 'Veiculos' in s), None)
        if veh_sheet:
            parsed_data['vehicle_fleet'] = ExcelParserService._parse_vehicle_fleet(excel_file, veh_sheet)
        else:
            parsed_data['vehicle_fleet'] = []
            warnings.append("Aba de Bens Móveis/Veículos não foi encontrada.")

        total_records = sum(len(parsed_data.get(k, [])) for k in ['debt_control', 'financial_investment', 'real_estate', 'livestock_inventory', 'vehicle_fleet'])
        if total_records == 0:
            raise ValueError("O arquivo Excel é válido, mas nenhuma estrutura conhecida de patrimônio foi encontrada ou todas estavam vazias.")

        summary_metrics = ExcelParserService._parse_summary_metrics(excel_file)
        if livestock_summary:
            summary_metrics['livestock'] = livestock_summary
        parsed_data['summary_metrics'] = summary_metrics
        parsed_data['warnings'] = warnings

        return parsed_data

    @staticmethod
    def _parse_summary_metrics(excel_file: pd.ExcelFile) -> Dict[str, Any]:
        """Extracts executive KPI metrics, variations, and weekly evolution table directly from Excel sheet cells."""
        metrics = {
            "weekly_variation_val": 0.0,
            "weekly_variation_pct": 0.0,
            "accumulated_variation_val": 0.0,
            "accumulated_variation_pct": 0.0,
            "cdi_weekly_pp": 0.0,
            "cdi_weekly_pct_cdi": 0.0,
            "cdi_accumulated_pp": 0.0,
            "cdi_accumulated_pct_cdi": 0.0,
            "weekly_evolution": [],
            "recebiveis": None,
            "category_yields": {}
        }

        # Extração de Recebíveis da aba Planilhão
        for sname in excel_file.sheet_names:
            if 'planilh' in sname.lower() or '1|' in sname:
                try:
                    df_p = pd.read_excel(excel_file, sheet_name=sname, header=None, nrows=15)
                    for r in range(len(df_p)):
                        for c in range(len(df_p.columns)):
                            if normalize_str(df_p.iloc[r, c]) == 'RECEBIVEIS':
                                for c_num in range(c + 1, len(df_p.columns)):
                                    num_v = clean_numeric(df_p.iloc[r, c_num])
                                    if num_v is not None and num_v > 0:
                                        metrics["recebiveis"] = num_v
                                        break
                                break
                        if metrics["recebiveis"] is not None:
                            break
                except Exception:
                    pass
                if metrics["recebiveis"] is not None:
                    break

        # Extração das taxas de rendimento por categoria da aba BI Celular
        for sname in excel_file.sheet_names:
            if 'celular' in sname.lower():
                try:
                    df_c = pd.read_excel(excel_file, sheet_name=sname, header=None, nrows=35)
                    hdr_row = None
                    col_cat = None
                    col_rendim = None
                    col_cdi = None
                    for r in range(len(df_c)):
                        row_vals = [normalize_str(x) for x in df_c.iloc[r].values if pd.notna(x)]
                        if 'CATEGORIA' in row_vals and any('VALOR' in x for x in row_vals):
                            hdr_row = r
                            for c in range(len(df_c.columns)):
                                c_val = normalize_str(df_c.iloc[r, c])
                                if 'CATEGORIA' in c_val:
                                    col_cat = c
                                elif 'RENDIM' in c_val and 'CDI' not in c_val:
                                    col_rendim = c
                                elif 'CDI' in c_val and ('RENDIM' in c_val or '2026' in c_val or '%' in c_val):
                                    col_cdi = c
                            break

                    if hdr_row is not None and col_cat is not None:
                        cat_yields = {}
                        for r in range(hdr_row + 1, min(hdr_row + 15, len(df_c))):
                            cat_name = df_c.iloc[r, col_cat]
                            if pd.isna(cat_name) or normalize_str(cat_name) == 'TOTAL':
                                break
                            norm_cat = normalize_str(cat_name)
                            clean_name = str(cat_name).replace('▸', '').replace('►', '').strip()
                            rendim_v = clean_numeric(df_c.iloc[r, col_rendim]) if col_rendim is not None else None
                            cdi_v = clean_numeric(df_c.iloc[r, col_cdi]) if col_cdi is not None else None

                            key = 'outro'
                            if 'PLANILH' in norm_cat: key = 'planilhao'
                            elif 'INVEST' in norm_cat: key = 'investimentos'
                            elif 'IMOVE' in norm_cat: key = 'imoveis'
                            elif 'GADO' in norm_cat: key = 'gado'
                            elif 'CAIXA' in norm_cat: key = 'caixa'
                            elif 'BENS' in norm_cat or 'MOVEIS' in norm_cat: key = 'bens_moveis'

                            cat_yields[key] = {
                                "name": clean_name,
                                "rendim_2026": rendim_v,
                                "rendim_cdi_2026": cdi_v
                            }
                        if cat_yields:
                            metrics["category_yields"] = cat_yields
                except Exception:
                    pass

        # Extração de variações e evolução semanal dos relatórios
        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None, nrows=60)
                for r in range(len(df)):
                    for c in range(len(df.columns) - 1):
                        cell_val = normalize_str(df.iloc[r, c])
                        next_val = df.iloc[r, c+1] if c+1 < len(df.columns) else None
                        
                        if 'VARIACAO SEMANAL' in cell_val:
                            val = clean_numeric(next_val)
                            if val is not None: metrics["weekly_variation_val"] = val
                        elif 'VARIACAO ACUMULADA' in cell_val:
                            val = clean_numeric(next_val)
                            if val is not None: metrics["accumulated_variation_val"] = val
                        elif 'CDI SEMANAL' in cell_val:
                            val = clean_numeric(next_val)
                            if val is not None: metrics["cdi_weekly_pp"] = val
                        elif 'CDI ACUMULADO' in cell_val:
                            val = clean_numeric(next_val)
                            if val is not None: metrics["cdi_accumulated_pp"] = val

                for r in range(len(df)):
                    row_str = " ".join([normalize_str(x) for x in df.iloc[r].values if pd.notna(x)])
                    if 'EVOLUCAO DO PATRIMONIO TOTAL' in row_str or ('SEMANA' in row_str and 'PATRIMONIO TOTAL' in row_str):
                        header_r = r
                        for offset in range(0, 3):
                            if r + offset < len(df):
                                h_row = [normalize_str(x) for x in df.iloc[r + offset].values if pd.notna(x)]
                                if any('SEMANA' in x for x in h_row) and any('DATA' in x or 'PATRIMONIO' in x for x in h_row):
                                    header_r = r + offset
                                    break
                        
                        weekly_list = []
                        for data_r in range(header_r + 1, min(header_r + 20, len(df))):
                            row_vals = df.iloc[data_r].values
                            clean_vals = [x for x in row_vals if pd.notna(x)]
                            if not clean_vals:
                                continue
                            
                            semana_num = None
                            dt_val = None
                            pat_val = None

                            for idx_cell, cell in enumerate(row_vals):
                                norm_c = normalize_str(cell)
                                if 'ALOCACAO' in norm_c or 'TOTAL' in norm_c:
                                    break
                                num_c = clean_numeric(cell)
                                parsed_d = parse_date(cell)

                                if num_c is not None and num_c <= 52 and semana_num is None and dt_val is None:
                                    semana_num = int(num_c)
                                elif parsed_d is not None and dt_val is None:
                                    dt_val = parsed_d
                                elif num_c is not None and num_c > 1000 and pat_val is None:
                                    pat_val = float(num_c)
                            
                            if 'ALOCACAO' in " ".join([normalize_str(x) for x in clean_vals]):
                                break

                            if pat_val is not None:
                                date_str = dt_val.strftime("%d/%b") if dt_val else (f"Semana {semana_num}" if semana_num else "Semana")
                                weekly_list.append({
                                    "semana_num": semana_num,
                                    "date_str": date_str,
                                    "patrimonio": pat_val
                                })
                        
                        if weekly_list:
                            metrics["weekly_evolution"] = weekly_list
                        break
            except Exception:
                continue

        return metrics


    @staticmethod
    def _parse_debt_control(excel_file: pd.ExcelFile, sheet_name: str) -> List[Dict[str, Any]]:
        df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
        h_idx = find_header_row(df_raw, ['DATA', 'SALDO INICIAL'])
        df = pd.read_excel(excel_file, sheet_name=sheet_name, skiprows=h_idx)
        
        col_map = {}
        for c in df.columns:
            nc = normalize_str(c)
            if nc == 'DATA': col_map['DATA'] = c
            elif 'SALDO INICIAL' in nc: col_map['SALDO INICIAL'] = c
            elif 'RECEBIMENTO' in nc: col_map['RECEBIMENTO'] = c
            elif 'DEVOLUCOES' in nc: col_map['DEVOLUÇÕES'] = c
            elif 'JUROS' in nc: col_map['JUROS'] = c
            elif 'SALDO FINAL' in nc: col_map['SALDO FINAL'] = c
            elif 'CDI' in nc: col_map['MÉD. % CDI'] = c

        records = []
        for _, row in df.iterrows():
            ref_date = parse_date(row.get(col_map.get('DATA')))
            if not ref_date:
                continue
                
            records.append({
                'reference_date': ref_date,
                'initial_balance': clean_numeric(row.get(col_map.get('SALDO INICIAL')), abs_val=True),
                'funding_amount': clean_numeric(row.get(col_map.get('RECEBIMENTO')), abs_val=True),
                'repayments': clean_numeric(row.get(col_map.get('DEVOLUÇÕES')), abs_val=True),
                'interest': clean_numeric(row.get(col_map.get('JUROS')), abs_val=True),
                'final_balance': clean_numeric(row.get(col_map.get('SALDO FINAL')), abs_val=True),
                'avg_cdi_percentage': clean_numeric(row.get(col_map.get('MÉD. % CDI')))
            })
        return records

    @staticmethod
    def _parse_financial_investment(excel_file: pd.ExcelFile, sheet_name: str) -> List[Dict[str, Any]]:
        df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
        h_idx = find_header_row(df_raw, ['ATIVO'])
        df = pd.read_excel(excel_file, sheet_name=sheet_name, skiprows=h_idx)

        asset_col = next((c for c in df.columns if 'ATIVO' in normalize_str(c)), df.columns[1] if len(df.columns) > 1 else df.columns[0])
        date_cols = [c for c in df.columns if parse_date(c) is not None]

        temp_list = []
        for _, row in df.iterrows():
            asset_name = str(row.get(asset_col, '')).strip()
            norm_name = normalize_str(asset_name)
            if not asset_name or norm_name in ['TOTAL', 'CHECK', 'NAN', 'NONE', 'INVESTIMENTOS', 'OFFSHORE (VB AGRO) - BTG'] or norm_name.startswith('TOTAL') or str(asset_col).startswith('Unnamed:'):
                continue

            for dc in date_cols:
                ref_date = parse_date(dc)
                amt = clean_numeric(row.get(dc))
                if ref_date and amt is not None:
                    temp_list.append({
                        'asset_name': asset_name,
                        'reference_date': ref_date,
                        'amount': amt
                    })

        totals_by_date: Dict[date, float] = {}
        for item in temp_list:
            d = item['reference_date']
            totals_by_date[d] = totals_by_date.get(d, 0.0) + item['amount']

        records = []
        for item in temp_list:
            d = item['reference_date']
            total = totals_by_date.get(d, 0.0)
            weight = (item['amount'] / total) if total > 0 else 0.0
            records.append({
                'asset_name': item['asset_name'],
                'reference_date': item['reference_date'],
                'amount': item['amount'],
                'portfolio_weight': round(weight, 4)
            })

        return records

    @staticmethod
    def _parse_real_estate(excel_file: pd.ExcelFile, sheet_name: str) -> List[Dict[str, Any]]:
        df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
        h_idx = find_header_row(df_raw, ['DESCRICAO', 'IMOVEL', 'VALOR'])
        df = pd.read_excel(excel_file, sheet_name=sheet_name, skiprows=h_idx)

        desc_col = next((c for c in df.columns if any(k in normalize_str(c) for k in ['DESCRICAO', 'IMOVEL', 'PROPERTY'])), df.columns[1] if len(df.columns) > 1 else df.columns[0])
        val_col = next((c for c in df.columns if 'VALOR' in normalize_str(c)), df.columns[2] if len(df.columns) > 2 else df.columns[1])

        records = []
        for _, row in df.iterrows():
            desc = str(row.get(desc_col, '')).strip()
            norm_desc = normalize_str(desc)
            if not desc or norm_desc.startswith('TOTAL') or norm_desc in ['NAN', 'NONE']:
                continue
            val = clean_numeric(row.get(val_col))
            if val is not None:
                records.append({
                    'description': desc,
                    'market_value': val
                })
        return records

    @staticmethod
    def _parse_livestock(excel_file: pd.ExcelFile, sheet_name: str) -> tuple[List[Dict[str, Any]], Dict[str, Any] | None]:
        df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)

        is_consolidated = False
        for _, row in df_raw.iterrows():
            row_str = " ".join([normalize_str(x) for x in row.values if pd.notna(x)])
            if 'DISTRIBUICAO POR LOCAL' in row_str or 'DISTRIBUICAO POR OPERADOR' in row_str or 'TOTAL DE CABECAS' in row_str:
                is_consolidated = True
                break

        if is_consolidated:
            return ExcelParserService._parse_livestock_consolidated(df_raw)
        else:
            return ExcelParserService._parse_livestock_detailed(df_raw), None

    @staticmethod
    def _parse_livestock_consolidated(df_raw: pd.DataFrame) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        kpis = {
            "total_cabecas": 0,
            "valor_rebanho": 0.0,
            "valor_medio_cabeca": 0.0,
            "peso_medio_cabeca": 0.0,
            "frete_total": 0.0,
            "comissao_total": 0.0,
            "investimento_total": 0.0,
        }

        def get_val_nearby(row_idx: int, col_idx: int) -> float | None:
            if row_idx + 1 < len(df_raw):
                v = clean_numeric(df_raw.iloc[row_idx + 1, col_idx])
                if v is not None:
                    return v
            if col_idx + 1 < len(df_raw.columns):
                v = clean_numeric(df_raw.iloc[row_idx, col_idx + 1])
                if v is not None:
                    return v
            if row_idx + 1 < len(df_raw) and col_idx + 1 < len(df_raw.columns):
                v = clean_numeric(df_raw.iloc[row_idx + 1, col_idx + 1])
                if v is not None:
                    return v
            return None

        for r in range(len(df_raw)):
            for c in range(len(df_raw.columns)):
                cell_norm = normalize_str(df_raw.iloc[r, c])
                if cell_norm == 'TOTAL DE CABECAS':
                    v = get_val_nearby(r, c)
                    if v is not None:
                        kpis["total_cabecas"] = int(v)
                elif cell_norm == 'VALOR DO REBANHO':
                    v = get_val_nearby(r, c)
                    if v is not None:
                        kpis["valor_rebanho"] = v
                elif cell_norm == 'VALOR MEDIO / CABECA':
                    v = get_val_nearby(r, c)
                    if v is not None:
                        kpis["valor_medio_cabeca"] = v
                elif cell_norm == 'PESO MEDIO / CABECA':
                    v = get_val_nearby(r, c)
                    if v is not None:
                        kpis["peso_medio_cabeca"] = v
                elif cell_norm == 'FRETE TOTAL':
                    v = get_val_nearby(r, c)
                    if v is not None:
                        kpis["frete_total"] = v
                elif cell_norm == 'COMISSAO TOTAL':
                    v = get_val_nearby(r, c)
                    if v is not None:
                        kpis["comissao_total"] = v
                elif 'INVESTIMENTO TOTAL' in cell_norm:
                    v = get_val_nearby(r, c)
                    if v is not None:
                        kpis["investimento_total"] = v

        dist_local = []
        for r in range(len(df_raw)):
            row_str = " ".join([normalize_str(x) for x in df_raw.iloc[r].values if pd.notna(x)])
            if 'DISTRIBUICAO POR LOCAL' in row_str:
                for data_r in range(r + 2, min(r + 10, len(df_raw))):
                    row_vals = df_raw.iloc[data_r].values
                    non_empty = [x for x in row_vals if pd.notna(x)]
                    if not non_empty:
                        continue
                    name = str(non_empty[0]).strip()
                    if normalize_str(name) == 'TOTAL':
                        break
                    cab = clean_numeric(non_empty[1]) if len(non_empty) > 1 else 0
                    pct_cab = clean_numeric(non_empty[2]) if len(non_empty) > 2 else 0
                    val = clean_numeric(non_empty[3]) if len(non_empty) > 3 else 0
                    pct_val = clean_numeric(non_empty[4]) if len(non_empty) > 4 else 0
                    dist_local.append({
                        "local": name,
                        "cabecas": int(cab or 0),
                        "pct_cabecas": pct_cab or 0.0,
                        "valor": val or 0.0,
                        "pct_valor": pct_val or 0.0
                    })

        dist_uf = []
        for r in range(len(df_raw)):
            row_str = " ".join([normalize_str(x) for x in df_raw.iloc[r].values if pd.notna(x)])
            if 'DISTRIBUICAO POR UF' in row_str:
                for data_r in range(r + 2, min(r + 10, len(df_raw))):
                    row_vals = df_raw.iloc[data_r].values
                    non_empty = [x for x in row_vals if pd.notna(x)]
                    if not non_empty:
                        continue
                    uf_name = str(non_empty[0]).strip()
                    if normalize_str(uf_name) == 'TOTAL':
                        break
                    cab = clean_numeric(non_empty[1]) if len(non_empty) > 1 else 0
                    val = clean_numeric(non_empty[2]) if len(non_empty) > 2 else 0
                    med = clean_numeric(non_empty[3]) if len(non_empty) > 3 else 0
                    pct_val = clean_numeric(non_empty[4]) if len(non_empty) > 4 else 0
                    dist_uf.append({
                        "uf": uf_name,
                        "cabecas": int(cab or 0),
                        "valor": val or 0.0,
                        "valor_medio": med or 0.0,
                        "pct_valor": pct_val or 0.0
                    })

        dist_operador = []
        for r in range(len(df_raw)):
            row_str = " ".join([normalize_str(x) for x in df_raw.iloc[r].values if pd.notna(x)])
            if 'DISTRIBUICAO POR OPERADOR' in row_str:
                for data_r in range(r + 2, min(r + 15, len(df_raw))):
                    row_vals = df_raw.iloc[data_r].values
                    non_empty = [x for x in row_vals if pd.notna(x)]
                    if not non_empty:
                        continue
                    op_name = str(non_empty[0]).strip()
                    if normalize_str(op_name) == 'TOTAL':
                        break
                    cab = clean_numeric(non_empty[1]) if len(non_empty) > 1 else 0
                    val = clean_numeric(non_empty[2]) if len(non_empty) > 2 else 0
                    med = clean_numeric(non_empty[3]) if len(non_empty) > 3 else 0
                    pct_val = clean_numeric(non_empty[4]) if len(non_empty) > 4 else 0
                    filtro = str(non_empty[5]).strip() if len(non_empty) > 5 else op_name
                    dist_operador.append({
                        "operador": op_name,
                        "cabecas": int(cab or 0),
                        "valor": val or 0.0,
                        "valor_medio": med or 0.0,
                        "pct_valor": pct_val or 0.0,
                        "filtro": filtro
                    })

        total_cab = kpis["total_cabecas"] or sum(op["cabecas"] for op in dist_operador) or 1
        frete_total = kpis["frete_total"] or 0.0
        comissao_total = kpis["comissao_total"] or 0.0
        peso_medio = kpis["peso_medio_cabeca"] or 0.0

        records = []
        accum_freight = 0.0
        accum_comm = 0.0

        for i, op in enumerate(dist_operador):
            is_last = (i == len(dist_operador) - 1)
            share = op["cabecas"] / total_cab if total_cab > 0 else 0

            if is_last:
                row_freight = round(frete_total - accum_freight, 2)
                row_comm = round(comissao_total - accum_comm, 2)
            else:
                row_freight = round(frete_total * share, 2)
                row_comm = round(comissao_total * share, 2)
                accum_freight += row_freight
                accum_comm += row_comm

            op_name = op["operador"]
            unit = f"{op_name}"
            loc_type = "Recria" if any(k in op_name.lower() for k in ['juina', 'juína', 'pura fé', 'pura fe', 'pasto']) else "Confinamento"
            if any(k in op_name.lower() for k in ['juina', 'juína', 'tripoloni']):
                unit += " - MT"
            elif any(k in op_name.lower() for k in ['pura f', 'adam']):
                unit += " - SP"
            elif 'jbs' in op_name.lower():
                unit += " - MS"

            records.append({
                "unit": unit,
                "owner": "VB AGRO",
                "location_type": loc_type,
                "contract_id": f"OP-{i+1:02d}",
                "cattle_partner": op_name,
                "head_count": op["cabecas"],
                "total_value": op["valor"],
                "avg_per_head": op["valor_medio"],
                "total_farm_weight": round(peso_medio, 2),
                "total_freight_per_head": row_freight,
                "total_commission": row_comm,
            })

        target_inv_total = round(kpis["investimento_total"], 2) if kpis["investimento_total"] else None
        if target_inv_total is not None and records:
            current_sum = sum(round(r["total_value"], 2) + r["total_freight_per_head"] + r["total_commission"] for r in records)
            diff = round(target_inv_total - current_sum, 2)
            if abs(diff) > 0 and abs(diff) < 0.10:
                records[-1]["total_freight_per_head"] = round(records[-1]["total_freight_per_head"] + diff, 2)

        livestock_summary = {
            "has_consolidated_summary": True,
            "total_cabecas": kpis["total_cabecas"],
            "valor_rebanho": kpis["valor_rebanho"],
            "valor_medio_cabeca": kpis["valor_medio_cabeca"],
            "peso_medio_cabeca": kpis["peso_medio_cabeca"],
            "frete_total": kpis["frete_total"],
            "comissao_total": kpis["comissao_total"],
            "investimento_total": kpis["investimento_total"],
            "distribuicao_local": dist_local,
            "distribuicao_uf": dist_uf,
            "distribuicao_operador": dist_operador,
        }
        return records, livestock_summary

    @staticmethod
    def _parse_livestock_detailed(df_raw: pd.DataFrame) -> List[Dict[str, Any]]:
        h_idx = find_header_row(df_raw, ['UNIDADE', 'LOCAL', 'ESTOQUE', 'PECUARISTA', 'PARCEIRO', 'CONTRATO'])
        df = df_raw.iloc[h_idx + 1:].copy()
        df.columns = df_raw.iloc[h_idx].values

        col_map = {}
        for c in df.columns:
            nc = normalize_str(c)
            if 'UNIDADE' in nc: col_map['unit'] = c
            elif any(k in nc for k in ['PROPRIETARIO', 'OWNER']): col_map['owner'] = c
            elif any(k in nc for k in ['LOCAL', 'ESTOQUE']): col_map['location_type'] = c
            elif 'CONTRATO' in nc: col_map['contract_id'] = c
            elif any(k in nc for k in ['PECUARISTA', 'PARCEIRO']): col_map['cattle_partner'] = c
            elif any(k in nc for k in ['BOIS', 'CABECAS']): col_map['head_count'] = c
            elif nc == 'R$' or 'VALOR TOTAL' in nc: col_map['total_value'] = c
            elif 'MEDIA CAB' in nc or 'MEDIA P/ CABECA' in nc: col_map['avg_per_head'] = c
            elif 'PESO' in nc: col_map['total_farm_weight'] = c
            elif 'FRETE' in nc: col_map['total_freight_per_head'] = c
            elif 'COMISSAO' in nc: col_map['total_commission'] = c

        records = []
        for _, row in df.iterrows():
            unit = str(row.get(col_map.get('unit'), '')).strip()
            norm_unit = normalize_str(unit)
            if not unit or norm_unit.startswith('TOTAL') or norm_unit in ['NAN', 'NONE']:
                continue
            records.append({
                'unit': unit,
                'owner': str(row.get(col_map.get('owner'), '')).strip() or None,
                'location_type': str(row.get(col_map.get('location_type'), '')).strip() or None,
                'contract_id': str(row.get(col_map.get('contract_id'), '')).strip() or None,
                'cattle_partner': str(row.get(col_map.get('cattle_partner'), '')).strip() or None,
                'head_count': int(clean_numeric(row.get(col_map.get('head_count'), 0)) or 0),
                'total_value': clean_numeric(row.get(col_map.get('total_value'), 0)),
                'avg_per_head': clean_numeric(row.get(col_map.get('avg_per_head'), 0)),
                'total_farm_weight': clean_numeric(row.get(col_map.get('total_farm_weight'), 0)),
                'total_freight_per_head': clean_numeric(row.get(col_map.get('total_freight_per_head'), 0)),
                'total_commission': clean_numeric(row.get(col_map.get('total_commission'), 0)),
            })
        return records

    @staticmethod
    def _parse_vehicle_fleet(excel_file: pd.ExcelFile, sheet_name: str) -> List[Dict[str, Any]]:
        df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
        records = []

        h_idx = find_header_row(df_raw, ['VEICULO', 'CHASSI', 'PLACA', 'ITEM'])
        df_veh = pd.read_excel(excel_file, sheet_name=sheet_name, skiprows=h_idx)

        col_map = {}
        for c in df_veh.columns:
            nc = normalize_str(c)
            if 'VEICULO' in nc or 'MAQUINA' in nc: col_map['vehicle_description'] = c
            elif 'ANO FAB' in nc: col_map['manufacture_year'] = c
            elif 'ANO MOD' in nc: col_map['model_year'] = c
            elif 'IDADE' in nc: col_map['age'] = c
            elif 'CHASSI' in nc: col_map['chassis'] = c
            elif 'PLACA' in nc: col_map['license_plate'] = c
            elif 'REGIAO' in nc or 'RISCO' in nc: col_map['risk_region'] = c
            elif 'PROPRIETARIO' in nc or 'USUARIO' in nc or 'DESTINADO' in nc: col_map['assigned_to'] = c
            elif 'VALOR DE MERCADO' in nc or 'VALOR FIPE' in nc: col_map['market_value'] = c
            elif 'PREMIO ANUAL' in nc: col_map['annual_premium'] = c
            elif 'IOF' in nc: col_map['iof_tax'] = c
            elif 'VALOR SEGURO' in nc: col_map['insurance_value'] = c
            elif 'TIPO SEGURO' in nc: col_map['insurance_type'] = c

        for _, row in df_veh.iterrows():
            item_val = clean_numeric(row.get('ITEM')) if 'ITEM' in df_veh.columns else 1
            desc = str(row.get(col_map.get('vehicle_description'), '')).strip()
            norm_desc = normalize_str(desc)
            
            if norm_desc.startswith('TOTAL') or norm_desc.startswith('AERONAVE') or norm_desc.startswith('RESUMO'):
                break
            if ('ITEM' in df_veh.columns and item_val is None) or not desc or norm_desc in ['NAN', 'NONE']:
                continue
                
            records.append({
                'vehicle_description': desc,
                'manufacture_year': int(clean_numeric(row.get(col_map.get('manufacture_year'))) or 0) or None,
                'model_year': int(clean_numeric(row.get(col_map.get('model_year'))) or 0) or None,
                'age': int(clean_numeric(row.get(col_map.get('age'))) or 0) or None,
                'chassis': str(row.get(col_map.get('chassis'), '')).strip() or None,
                'license_plate': str(row.get(col_map.get('license_plate'), '')).strip() or None,
                'risk_region': str(row.get(col_map.get('risk_region'), '')).strip() or None,
                'assigned_to': str(row.get(col_map.get('assigned_to'), '')).strip() or None,
                'market_value': clean_numeric(row.get(col_map.get('market_value'))),
                'annual_premium': clean_numeric(row.get(col_map.get('annual_premium'))),
                'iof_tax': clean_numeric(row.get(col_map.get('iof_tax'))),
                'insurance_value': clean_numeric(row.get(col_map.get('insurance_value'))),
                'insurance_type': str(row.get(col_map.get('insurance_type'), '')).strip() or None,
            })

        in_aeronave_block = False
        for _, row in df_raw.iterrows():
            vals = [normalize_str(x) for x in row.values if pd.notna(x)]
            if 'AERONAVE' in vals:
                in_aeronave_block = True
                continue
            if in_aeronave_block:
                if any('RESUMO' in v for v in vals) or any('PROPRIETARIO' in v for v in vals):
                    in_aeronave_block = False
                    break
                row_list = row.values.tolist()
                plane_name = str(row_list[2]).strip() if pd.notna(row_list[2]) else None
                norm_plane = normalize_str(plane_name)
                if not plane_name or norm_plane.startswith('TOTAL') or norm_plane in ['NAN', 'NONE']:
                    continue
                    
                usd_val = clean_numeric(row_list[9]) if len(row_list) > 9 else None
                brl_val = clean_numeric(row_list[10]) if len(row_list) > 10 else None
                
                if brl_val is not None and brl_val > 0:
                    records.append({
                        'vehicle_description': f"AERONAVE - {plane_name}",
                        'manufacture_year': None,
                        'model_year': None,
                        'age': None,
                        'chassis': None,
                        'license_plate': None,
                        'risk_region': 'AÉREO',
                        'assigned_to': 'VNMB',
                        'market_value': brl_val,
                        'annual_premium': None,
                        'iof_tax': None,
                        'insurance_value': usd_val,
                        'insurance_type': 'AERONAVE',
                    })

        return records
