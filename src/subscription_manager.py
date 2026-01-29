"""Subscription manager for real-time notifications"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional, List, Any


@dataclass
class SubscriptionInfo:
    """Information about an active subscription"""
    connection: Any
    token: str
    subscribed_at: datetime
    ip_address: str
    last_activity: datetime


class SubscriptionManager:
    """Manages active subscriptions for real-time notifications"""

    def __init__(self):
        self.subscriptions: Dict[int, Dict[str, SubscriptionInfo]] = {}

    def add(
        self,
        account_id: int,
        sub_id: str,
        connection: Any,
        token: str,
        ip_address: str
    ) -> None:
        """Add new subscription"""

        now = datetime.now(timezone.utc)

        if account_id not in self.subscriptions:
            self.subscriptions[account_id] = {}

        self.subscriptions[account_id][sub_id] = SubscriptionInfo(
            connection=connection,
            token=token,
            subscribed_at=now,
            ip_address=ip_address,
            last_activity=now
        )

    def remove(self, account_id: int, sub_id: str) -> bool:
        """Remove subscription by account_id and sub_id"""

        if account_id not in self.subscriptions:
            return False

        if sub_id not in self.subscriptions[account_id]:
            return False

        del self.subscriptions[account_id][sub_id]

        if not self.subscriptions[account_id]:
            del self.subscriptions[account_id]

        return True

    def is_online(self, account_id: int) -> bool:
        """Check if account has any active subscriptions"""

        return account_id in self.subscriptions and len(self.subscriptions[account_id]) > 0

    def is_token_online(self, token: str) -> bool:
        """Check if token has any active subscriptions"""

        for subs in self.subscriptions.values():
            for info in subs.values():
                if info.token == token:
                    return True

        return False

    def update_activity(self, account_id: int, sub_id: str) -> bool:
        """Update last_activity timestamp for subscription"""

        if account_id not in self.subscriptions:
            return False

        if sub_id not in self.subscriptions[account_id]:
            return False

        self.subscriptions[account_id][sub_id].last_activity = datetime.now(timezone.utc)
        return True

    def get_subscriptions_by_account(self, account_id: int) -> List[str]:
        """Get all subscription IDs for account"""

        if account_id not in self.subscriptions:
            return []

        return list(self.subscriptions[account_id].keys())

    def get_subscriptions_by_token(self, token: str) -> List[tuple[int, str]]:
        """Get all (account_id, sub_id) pairs for token"""

        result = []

        for account_id, subs in self.subscriptions.items():
            for sub_id, info in subs.items():
                if info.token == token:
                    result.append((account_id, sub_id))

        return result

    def get_subscription_info(self, account_id: int, sub_id: str) -> Optional[SubscriptionInfo]:
        """Get subscription info by account_id and sub_id"""

        if account_id not in self.subscriptions:
            return None

        return self.subscriptions[account_id].get(sub_id)

    async def notify(self, account_id: int, data: Any) -> int:
        """Send notification to all subscriptions for account, returns count of notified connections"""

        if account_id not in self.subscriptions:
            return 0

        count = 0
        failed_subs = []

        for sub_id, info in self.subscriptions[account_id].items():
            try:
                await info.connection.send(data)
                count += 1
            except Exception:
                failed_subs.append(sub_id)

        for sub_id in failed_subs:
            self.remove(account_id, sub_id)

        return count

    def get_all_accounts(self) -> List[int]:
        """Get list of all account IDs with active subscriptions"""

        return list(self.subscriptions.keys())

    def get_subscription_count(self, account_id: int) -> int:
        """Get number of active subscriptions for account"""

        if account_id not in self.subscriptions:
            return 0

        return len(self.subscriptions[account_id])

    def get_total_subscriptions(self) -> int:
        """Get total number of active subscriptions across all accounts"""

        return sum(len(subs) for subs in self.subscriptions.values())
