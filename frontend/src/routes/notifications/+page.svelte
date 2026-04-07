<script lang="ts">
    import { onMount } from "svelte";
    import { Card, CardContent } from "$lib/components/ui/card";
    import { Badge } from "$lib/components/ui/badge";
    import { Separator } from "$lib/components/ui/separator";
    import { apiFetch } from "$lib/api";

    type NotificationType = "approved" | "denied" | "cancelled";

    interface Notification {
        id: number;
        userID: string;
        bookingID: number;
        message: string;
        type: NotificationType;
        isRead: boolean;
        createdAt: string;
    }

    let notifications: Notification[] = $state([]);
    let unreadCount: number = $state(0);
    let loading: boolean = $state(true);
    let error: string = $state("");

    onMount(async () => {
        await Promise.all([fetchNotifications(), fetchUnreadCount()]);
        loading = false;

        const interval = setInterval(async () => {
            await Promise.all([fetchNotifications(), fetchUnreadCount()]);
        }, 5000);

        return () => clearInterval(interval);
    });

    async function fetchNotifications() {
        try {
            const data = await apiFetch<Notification[]>("/api/notifications");
            //newest notification first
            notifications = data.sort(
                (a, b) =>
                    new Date(b.createdAt).getTime() -
                    new Date(a.createdAt).getTime(),
            );
        } catch (e) {
            error = "Could not load notifications. Please try again.";
        }
    }

    async function fetchUnreadCount() {
        try {
            const data = await apiFetch<{ count: number }>(
                "/api/notifications/unread-count",
            );
            unreadCount = data.count ?? 0;
        } catch {
            // unread count is non-critical
        }
    }

    async function markAsRead(notification: Notification) {
        if (notification.isRead) return;

        //update
        notification.isRead = true;
        notifications = notifications;
        unreadCount = Math.max(0, unreadCount - 1);

        try {
            await apiFetch(`/api/notifications/${notification.id}/read`, {
                method: "PATCH",
            });
        } catch {
            // Revert on failure
            notification.isRead = false;
            notifications = notifications;
            unreadCount += 1;
        }
    }

    // specifies green/red/neutral for each notification
    function badgeClass(type: NotificationType): string {
        if (type === "approved")
            return "border-green-500/50 bg-green-500/10 text-green-700 dark:text-green-400";
        if (type === "denied")
            return "border-red-500/50 bg-red-500/10 text-red-700 dark:text-red-400";
        return "border-border bg-muted/50 text-muted-foreground";
    }

    function formatDate(iso: string): string {
        const date = new Date(iso);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHour = Math.floor(diffMin / 60);
        const diffDay = Math.floor(diffHour / 24);

        if (diffSec < 60) return "Just now";
        if (diffMin < 60) return `${diffMin}m ago`;
        if (diffHour < 24) return `${diffHour}h ago`;
        if (diffDay < 7) return `${diffDay}d ago`;

        return date.toLocaleDateString("en-CA", {
            year: "numeric",
            month: "short",
            day: "numeric",
        });
    }

    function typeLabel(type: NotificationType): string {
        return type.charAt(0).toUpperCase() + type.slice(1);
    }
</script>

<div class="flex flex-1 flex-col gap-6 p-6">
    <!-- Header -->
    <div>
        <div class="flex items-center gap-2">
            <h1 class="text-2xl font-semibold tracking-tight">Notifications</h1>
            {#if unreadCount > 0}
                <span
                    class="inline-flex items-center justify-center min-w-5 h-5 px-1.5 rounded-full text-xs font-bold bg-primary text-primary-foreground"
                    aria-label="{unreadCount} unread notifications"
                >
                    {unreadCount}
                </span>
            {/if}
        </div>
        <p class="text-muted-foreground text-sm">
            Your booking updates and alerts.
        </p>
    </div>

    <Separator />

    {#if loading}
        <div class="flex flex-col gap-3">
            {#each Array(4) as _}
                <div
                    class="rounded-xl border bg-card p-4 flex flex-col gap-2 animate-pulse"
                >
                    <div class="h-3 rounded-full bg-muted w-4/5"></div>
                    <div class="h-3 rounded-full bg-muted w-2/5"></div>
                    <div class="h-3 rounded-full bg-muted w-1/3"></div>
                </div>
            {/each}
        </div>
    {:else if error}
        <div
            class="text-muted-foreground flex flex-1 items-center justify-center text-sm"
        >
            {error}
        </div>
    {:else if notifications.length === 0}
        <div
            class="text-muted-foreground flex flex-1 items-center justify-center text-sm"
        >
            No notifications yet. When your bookings are approved, denied, or
            cancelled, you'll see updates here.
        </div>
    {:else}
        <ul class="flex flex-col gap-3" aria-label="Notifications">
            {#each notifications as notification (notification.id)}
                <li>
                    <button
                        class="w-full text-left disabled:cursor-default"
                        disabled={notification.isRead}
                        onclick={() => markAsRead(notification)}
                    >
                        <Card
                            class="transition-all duration-150 {notification.isRead
                                ? 'opacity-60'
                                : 'border-primary/30 bg-primary/[0.02] hover:shadow-md hover:-translate-y-px cursor-pointer'}"
                        >
                            <CardContent class="flex items-start gap-3 p-4">
                                <!-- Unread/read dot indicator -->
                                <div class="pt-1 shrink-0" aria-hidden="true">
                                    {#if !notification.isRead}
                                        <span
                                            class="block w-2 h-2 rounded-full bg-primary ring-2 ring-primary/20"
                                        ></span>
                                    {:else}
                                        <span
                                            class="block w-2 h-2 rounded-full bg-muted"
                                        ></span>
                                    {/if}
                                </div>

                                <div class="flex-1 min-w-0 flex flex-col gap-1">
                                    <div
                                        class="flex items-start justify-between gap-3"
                                    >
                                        <!-- Message (bold when unread) -->
                                        <p
                                            class="text-sm leading-snug {notification.isRead
                                                ? 'font-normal'
                                                : 'font-semibold'}"
                                        >
                                            {notification.message}
                                        </p>

                                        <!-- Type badge: green=approved, red=denied, neutral=cancelled -->
                                        <Badge
                                            variant="outline"
                                            class="shrink-0 text-xs uppercase tracking-wide {badgeClass(
                                                notification.type,
                                            )}"
                                        >
                                            {typeLabel(notification.type)}
                                        </Badge>
                                    </div>

                                    <!-- Timestamp -->
                                    <time
                                        class="text-xs text-muted-foreground"
                                        datetime={notification.createdAt}
                                        title={new Date(
                                            notification.createdAt,
                                        ).toLocaleString()}
                                    >
                                        {formatDate(notification.createdAt)}
                                    </time>
                                </div>
                            </CardContent>
                        </Card>
                    </button>
                </li>
            {/each}
        </ul>
    {/if}
</div>
