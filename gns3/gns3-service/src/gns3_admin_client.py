# Re-export-фасад для обратной совместимости импортов.
#
# Реализация переехала в src/clients/admin/. Этот модуль оставлен, чтобы не
# ломать тесты и сторонних потребителей, импортирующих из src.gns3_admin_client.

from src.clients.admin import GNS3AdminClient

__all__ = ["GNS3AdminClient"]
