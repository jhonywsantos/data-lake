from pipeline.bronze import executar_bronze
from pipeline.prata import executar_prata
from pipeline.ouro import executar_ouro

if __name__ == "__main__":
    print("=== INICIANDO PIPELINE MEDALHÃO (MOVIELENS) ===")
    executar_bronze()
    executar_prata()
    executar_ouro()
    print("=== PIPELINE CONCLUÍDO COM SUCESSO ===")
