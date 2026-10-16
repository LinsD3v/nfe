# worker/main.py

import subprocess
from repositories.orders import (
    atualizar_status,
    buscar_pedidos_por_status,
)

def processar_pedidos():
    pedidos = buscar_pedidos_por_status("pending", True)
    
    for pedido in pedidos:
        order_id = pedido["order_id"]

        try:
            print(f"Processando pedido {order_id}")

            # 1. Atualizar status para processing
            atualizar_status(order_id, "processing")

            # 2. Executar as etapas da automação
            # subprocess.run(...)

            # 3. Validar o resultado da emissão
            # 4. Atualizar para completed ou error

        except Exception as erro:
            print(f"Erro no pedido {order_id}: {erro}")
            atualizar_status(order_id, "error")

if __name__ == "__main__":
    processar_pedidos()
