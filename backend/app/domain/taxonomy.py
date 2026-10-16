from enum import Enum
from pydantic import BaseModel, Field

class TopicSlug(str, Enum):
    # Authentication & Access
    LOGIN_AUTH = "login_auth"
    ACCOUNT_MANAGEMENT = "account_management"
    
    # Billing & Monetization
    BILLING_PRICING = "billing_pricing"
    SUBSCRIPTION_CANCELLATION = "subscription_cancellation"
    REFUND_PAYMENT = "refund_payment"
    
    # App Reliability & Performance
    APP_CRASH = "app_crash"
    SLOW_PERFORMANCE = "slow_performance"
    BATTERY_DRAIN = "battery_drain"
    OFFLINE_SYNC = "offline_sync"
    
    # User Interface & Experience
    UI_NAVIGATION = "ui_navigation"
    FEATURE_DISCOVERABILITY = "feature_discoverability"
    NOTIFICATION_OVERLOAD = "notification_overload"
    DARK_MODE_DESIGN = "dark_mode_design"
    
    # Core Functionality & Features
    SEARCH_RETRIEVAL = "search_retrieval"
    EXPORT_IMPORT = "export_import"
    INTEGRATIONS_API = "integrations_api"
    
    # Service & Support
    CUSTOMER_SUPPORT = "customer_support"
    DOCUMENTATION = "documentation"
    
    # Catch-all
    OTHER = "other"


class TopicDefinition(BaseModel):
    slug: TopicSlug
    label: str
    category: str
    description: str
    positive_example: str
    negative_example: str


CONTROLLED_TAXONOMY: dict[TopicSlug, TopicDefinition] = {
    TopicSlug.LOGIN_AUTH: TopicDefinition(
        slug=TopicSlug.LOGIN_AUTH,
        label="Login & Authentication",
        category="Access",
        description="Issues related to signing in, biometric login, password resets, 2FA, session timeouts.",
        positive_example="FaceID never works on iOS 18, forced to retype my master password 10 times a day.",
        negative_example="Cannot find where to change my billing email."
    ),
    TopicSlug.ACCOUNT_MANAGEMENT: TopicDefinition(
        slug=TopicSlug.ACCOUNT_MANAGEMENT,
        label="Account Management",
        category="Access",
        description="Profile settings, team member permissions, org switching, account deletion.",
        positive_example="Unable to invite new team members to our organization workspace.",
        negative_example="Can't log in because of a 500 error."
    ),
    TopicSlug.BILLING_PRICING: TopicDefinition(
        slug=TopicSlug.BILLING_PRICING,
        label="Billing & Pricing",
        category="Billing",
        description="Price increases, tiers, currency conversion, invoice generation, enterprise quotes.",
        positive_example="The 40% sudden price hike without prior email notice is completely unacceptable.",
        negative_example="I asked support for a refund and got no reply."
    ),
    TopicSlug.SUBSCRIPTION_CANCELLATION: TopicDefinition(
        slug=TopicSlug.SUBSCRIPTION_CANCELLATION,
        label="Subscription & Cancellation",
        category="Billing",
        description="Difficulty pausing or canceling subscriptions, auto-renewal surprises.",
        positive_example="They bury the cancel subscription button inside 6 nested menus.",
        negative_example="My credit card expired so billing failed."
    ),
    TopicSlug.REFUND_PAYMENT: TopicDefinition(
        slug=TopicSlug.REFUND_PAYMENT,
        label="Refunds & Payment Processing",
        category="Billing",
        description="Double charges, failed credit card payments, pending refunds, chargebacks.",
        positive_example="Was charged twice for the annual plan and support hasn't processed my refund.",
        negative_example="Too expensive compared to competitor."
    ),
    TopicSlug.APP_CRASH: TopicDefinition(
        slug=TopicSlug.APP_CRASH,
        label="App Crash & Freezes",
        category="Reliability",
        description="Fatal crashes, unexpected app exits, frozen blank screens, unhandled exceptions.",
        positive_example="App consistently crashes immediately after opening the camera scanner.",
        negative_example="App takes 5 seconds to load the dashboard."
    ),
    TopicSlug.SLOW_PERFORMANCE: TopicDefinition(
        slug=TopicSlug.SLOW_PERFORMANCE,
        label="Slow Performance & Latency",
        category="Reliability",
        description="Sluggish interactions, spinning loaders, high latency, laggy UI animations.",
        positive_example="Scrolling through more than 50 items causes extreme stutter and 4-second hangs.",
        negative_example="The app crashed with an error dialog."
    ),
    TopicSlug.BATTERY_DRAIN: TopicDefinition(
        slug=TopicSlug.BATTERY_DRAIN,
        label="Battery & Resource Drain",
        category="Reliability",
        description="Excessive battery usage, device heating, background CPU/memory consumption.",
        positive_example="Left the app in background for 2 hours and my phone lost 35% battery and felt hot.",
        negative_example="App crashed when opening."
    ),
    TopicSlug.OFFLINE_SYNC: TopicDefinition(
        slug=TopicSlug.OFFLINE_SYNC,
        label="Offline Mode & Sync",
        category="Reliability",
        description="Conflicts during sync, loss of offline edits, network reconnection failures.",
        positive_example="Took notes on the plane without wifi and everything got wiped upon landing.",
        negative_example="Search query returned 0 results."
    ),
    TopicSlug.UI_NAVIGATION: TopicDefinition(
        slug=TopicSlug.UI_NAVIGATION,
        label="UI & Navigation",
        category="UX",
        description="Confusing layout, tiny touch targets, broken tabs, cluttered menu structures.",
        positive_example="The new bottom navigation hides the most important reports under an ellipsis.",
        negative_example="The app crashed when I tapped the button."
    ),
    TopicSlug.FEATURE_DISCOVERABILITY: TopicDefinition(
        slug=TopicSlug.FEATURE_DISCOVERABILITY,
        label="Feature Discoverability",
        category="UX",
        description="Users cannot locate existing features, onboarding confusion, lack of tooltips.",
        positive_example="Took me three weeks to realize you can bulk select records by long-pressing.",
        negative_example="The export CSV feature is broken."
    ),
    TopicSlug.NOTIFICATION_OVERLOAD: TopicDefinition(
        slug=TopicSlug.NOTIFICATION_OVERLOAD,
        label="Notification Overload & Spam",
        category="UX",
        description="Excessive push notifications, marketing spam, inability to configure alert channels.",
        positive_example="Sending me 4 marketing push alerts every single morning made me uninstall.",
        negative_example="I didn't receive the password reset code."
    ),
    TopicSlug.DARK_MODE_DESIGN: TopicDefinition(
        slug=TopicSlug.DARK_MODE_DESIGN,
        label="Dark Mode & Visual Design",
        category="UX",
        description="Color contrast, dark mode readability, font sizes, aesthetics.",
        positive_example="In dark mode, gray text on black background is completely unreadable.",
        negative_example="App is slow to respond."
    ),
    TopicSlug.SEARCH_RETRIEVAL: TopicDefinition(
        slug=TopicSlug.SEARCH_RETRIEVAL,
        label="Search & Filter Retrieval",
        category="Features",
        description="Keyword search misses obvious items, filter dropdowns fail, sorting bugs.",
        positive_example="Search never finds customer names with hyphens or apostrophes.",
        negative_example="Support was unhelpful when I asked how to search."
    ),
    TopicSlug.EXPORT_IMPORT: TopicDefinition(
        slug=TopicSlug.EXPORT_IMPORT,
        label="Export & Import",
        category="Features",
        description="CSV/PDF export corrupted, Excel formatting broken, import column mapping errors.",
        positive_example="PDF export truncates long table rows and generates blank pages.",
        negative_example="App is slow."
    ),
    TopicSlug.INTEGRATIONS_API: TopicDefinition(
        slug=TopicSlug.INTEGRATIONS_API,
        label="Integrations & API",
        category="Features",
        description="Slack, Zapier, Webhook, REST API rate limits, third-party authentication sync.",
        positive_example="The Salesforce integration stopped syncing leads after yesterday's v4.2 update.",
        negative_example="I want a discount on my monthly plan."
    ),
    TopicSlug.CUSTOMER_SUPPORT: TopicDefinition(
        slug=TopicSlug.CUSTOMER_SUPPORT,
        label="Customer Support Quality",
        category="Support",
        description="Unresponsive agents, generic bot replies, slow resolution times, ticket closures.",
        positive_example="Submitted a ticket 8 days ago, received only automated canned responses.",
        negative_example="The product has a bug in the export tool."
    ),
    TopicSlug.DOCUMENTATION: TopicDefinition(
        slug=TopicSlug.DOCUMENTATION,
        label="Documentation & Guides",
        category="Support",
        description="Outdated help center articles, missing API references, misleading screenshots.",
        positive_example="The webhook documentation lists endpoints that return 404.",
        negative_example="Support rep was rude."
    ),
    TopicSlug.OTHER: TopicDefinition(
        slug=TopicSlug.OTHER,
        label="Other / Unclassified",
        category="Miscellaneous",
        description="Feedback that does not map to any defined taxonomy category.",
        positive_example="I wish the app icon had a cat instead of an arrow.",
        negative_example="The app crashes on startup."
    ),
}

TAXONOMY_VERSION = "v1"
VALID_TOPIC_SLUGS = set(CONTROLLED_TAXONOMY.keys())
