import pandas as pd
import numpy as np

def generate_sample_excel(filename="sample_wealth_data.xlsx"):
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Sheet 1: 1| Planilhão (skiprows=2)
        sheet1_header = [
            ["RELATÓRIO DE CONTROLE DE DÍVIDAS", "", "", "", "", "", ""],
            ["Data de Emissão: 2026-08-11", "", "", "", "", "", ""],
            ["DATA", "SALDO INICIAL", "RECEBIMENTO", "DEVOLUÇÕES", "JUROS", "SALDO FINAL", "MÉD. % CDI"]
        ]
        sheet1_data = [
            ["01/01/2026", 1000000.00, 200000.00, 50000.00, 12000.00, 1162000.00, 0.1050],
            ["01/02/2026", 1162000.00, 0.00, 100000.00, 11500.00, 1073500.00, 0.1045],
            ["TOTAL", 2162000.00, 200000.00, 150000.00, 23500.00, 2235500.00, None]
        ]
        df1 = pd.DataFrame(sheet1_header + sheet1_data)
        df1.to_excel(writer, sheet_name="1| Planilhão", index=False, header=False)

        # Sheet 2: 2| Investimentos Financeiros (skiprows=2)
        sheet2_header = [
            ["POSIÇÃO DE INVESTIMENTOS FINANCEIROS", "", "", ""],
            ["Consolidado Por Mês", "", "", ""],
            ["Ativo", "12/2025", "01/2026", "02/2026"]
        ]
        sheet2_data = [
            ["Fundo Renda Fixa", 500000.00, 510000.00, 520000.00],
            ["Ações Ibovespa", 300000.00, 290000.00, 310000.00],
            ["CDB Prefixado", 200000.00, 202000.00, 204000.00],
            ["Total", 1000000.00, 1002000.00, 1034000.00]
        ]
        df2 = pd.DataFrame(sheet2_header + sheet2_data)
        df2.to_excel(writer, sheet_name="2| Investimentos Financeiros", index=False, header=False)

        # Sheet 3: 3| Imóveis (skiprows=0)
        sheet3_data = {
            "Imóvel": ["Fazenda Bela Vista", "Apartamento São Paulo", "Galpão Logístico"],
            "Valor de Mercado": [15000000.00, 2500000.00, 5000000.00]
        }
        df3 = pd.DataFrame(sheet3_data)
        df3.to_excel(writer, sheet_name="3| Imóveis", index=False)

        # Sheet 4: 4| Gado (skiprows=1)
        sheet4_header = [
            ["INVENTÁRIO DE GADO", "", "", "", "", "", "", "", "", "", ""],
            ["Unidade", "Proprietário", "Tipo Local", "Contrato", "Parceiro", "Cabeças", "Valor Total", "Média p/ Cabeça", "Peso Fazenda", "Frete p/ Cabeça", "Comissão Total"]
        ]
        sheet4_data = [
            ["Fazenda 1", "João Silva", "Confinamento", "CTR-001", "Parceria A", 500, 2500000.00, 5000.00, 220000.00, 50.00, 12500.00],
            ["Fazenda 2", "Maria Santos", "Pasto", "CTR-002", "Parceria B", 300, 1350000.00, 4500.00, 130000.00, 45.00, 6750.00],
            ["TOTAL", "", "", "", "", 800, 3850000.00, 4750.00, 350000.00, None, 19250.00]
        ]
        df4 = pd.DataFrame(sheet4_header + sheet4_data)
        df4.to_excel(writer, sheet_name="4| Gado", index=False, header=False)

        # Sheet 5: 5| Bens Móveis (skiprows=3)
        sheet5_header = [
            ["RELATÓRIO DE BENS MÓVEIS E VEÍCULOS", "", "", "", "", "", "", "", "", "", "", "", ""],
            ["Frota Atualizada", "", "", "", "", "", "", "", "", "", "", "", ""],
            ["Data: 2026", "", "", "", "", "", "", "", "", "", "", "", ""],
            ["Veículo", "Ano Fab", "Ano Mod", "Idade", "Chassi", "Placa", "Região Risco", "Destinado a", "Valor FIPE", "Prêmio Anual", "IOF", "Valor Segurado", "Tipo Seguro"]
        ]
        sheet5_data = [
            ["Toyota Hilux 4x4", 2023, 2024, 2, "9BRBH333", "ABC1D23", "Interior SP", "Diretoria", 250000.00, 8500.00, 620.00, 250000.00, "Comprehensive"],
            ["Trator John Deere 6110J", 2022, 2022, 4, "1JD6110", "TRA1234", "Rural", "Operação Farm", 420000.00, 12000.00, 880.00, 420000.00, "Machinery"],
            ["Total", None, None, None, "", "", "", "", 670000.00, 20500.00, 1500.00, 670000.00, ""]
        ]
        df5 = pd.DataFrame(sheet5_header + sheet5_data)
        df5.to_excel(writer, sheet_name="5| Bens Móveis", index=False, header=False)

    print(f"Generated sample Excel file: '{filename}' successfully!")

if __name__ == "__main__":
    generate_sample_excel()
