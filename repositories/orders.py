import json

from database import get_connection


def registrar_pedido(sale_id: str, payload: dict) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO nfe_data (
                order_id,
                status,
                payload,
                created_at,
                updated_at
            )
            VALUES (
                ?, 'pending', ?, 
                strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
                strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            )
            ON CONFLICT(order_id) DO NOTHING
            """,
            (sale_id, json.dumps(payload, ensure_ascii=False)),
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
