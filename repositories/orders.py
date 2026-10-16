import json

from database import get_connection


def registrar_pedido(sale_id: str, payload: dict, status: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO nfe_data (
                order_id,
                status,
                payload,
                created_at,
                updated_at,
                package_count,
                should_emit
            )
            VALUES (
                ?, ?, ?,
                strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
                strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
                ?, ?
            )
            ON CONFLICT(order_id) DO NOTHING
            """,
            (
                sale_id,
                status,
                json.dumps(payload, ensure_ascii=False),
                payload.get("package_count", 1),
                int(payload["should_emit"]),
            ),
        )

        return cursor.rowcount == 1


def buscar_pedido(sale_id: str):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM nfe_data WHERE order_id = ?",
            (sale_id,),
        ).fetchone()

        if row is None:
            return None

        pedido = dict(row)
        pedido["payload"] = json.loads(pedido["payload"])
        return pedido

def buscar_pedidos_por_status(status: str, should_emit: bool):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM nfe_data
            WHERE status = ?
              AND should_emit = ?
            """,
            (status, should_emit),
        ).fetchall()

        pedidos = []
        for row in rows:
            pedido = dict(row)
            pedido["payload"] = json.loads(pedido["payload"])
            pedidos.append(pedido)

        return pedidos


def atualizar_status(sale_id: str, status: str):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE nfe_data
            SET status = ?,
                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE order_id = ?
            """,
            (status, sale_id),
        )

        return cursor.rowcount == 1



def receber_pedido(sale_id: str, payload: dict) -> dict:
    package_count = payload.get("package_count", 1)

    # Mais de um pacote: bloquear emissão automática
    should_emit = package_count == 1
    status = "pending" if should_emit else "blocked"

    payload["should_emit"] = should_emit

    inserido = registrar_pedido(sale_id, payload, status)

    if not inserido:
        pedido = buscar_pedido(sale_id)

        return {
            "Accepted": False,
            "Reason": "duplicate",
            "pedido": pedido["status"] if pedido else "unknown",
        }

    return {
        "Accepted": True,
        "Status": status,
        "ShouldEmit": should_emit,
        "PackageCount": package_count,
    }
