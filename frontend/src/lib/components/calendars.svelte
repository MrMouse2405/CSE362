<script lang="ts">
    import * as Sidebar from "$lib/components/ui/sidebar/index.js";
    import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
    import { Badge } from "$lib/components/ui/badge/index.js";
    import EllipsisIcon from "@lucide/svelte/icons/ellipsis";
    import { Button } from "$lib/components/ui/button/index.js";
    import { goto } from "$app/navigation";
    import { apiFetch } from "$lib/api";

    interface TimeSlotResponse {
        id: number;
        room_id: number;
        slot_date: string;
        start_time: string;
        end_time: string;
        status: string;
    }

    interface BookingResponse {
        id: number;
        roomID: number;
        status: string;
        createdAt: string;
        timeSlots: TimeSlotResponse[];
    }

    interface RoomBasic {
        id: number;
        name: string;
        capacity: number;
    }

    interface BookingSummary {
        id: number;
        roomName: string;
        status: string;
        date: string;
        slotCount: number;
    }

    let bookings = $state<BookingSummary[]>([]);
    let loading = $state(true);

    $effect(() => {
        loadBookings();
    });

    async function loadBookings() {
        loading = true;
        try {
            const data = await apiFetch<BookingResponse[]>("/api/bookings");
            const recent = data.slice(0, 8); // show up to 8 most recent

            const roomIds = [...new Set(recent.map((b) => b.roomID))];
            const roomMap = new Map<number, string>();
            await Promise.all(
                roomIds.map(async (rid) => {
                    try {
                        const room = await apiFetch<RoomBasic>(
                            `/api/rooms/${rid}`,
                        );
                        roomMap.set(rid, room.name);
                    } catch {
                        roomMap.set(rid, `#${rid}`);
                    }
                }),
            );

            bookings = recent.map((b) => ({
                id: b.id,
                roomName: roomMap.get(b.roomID) ?? `#${b.roomID}`,
                status: b.status,
                date: b.timeSlots[0]?.slot_date ?? "—",
                slotCount: b.timeSlots.length,
            }));
        } catch {
            bookings = [];
        } finally {
            loading = false;
        }
    }

    function badgeVariant(
        status: string,
    ): "default" | "secondary" | "outline" | "destructive" {
        switch (status) {
            case "approved":
                return "default";
            case "pending":
                return "secondary";
            case "denied":
                return "destructive";
            default:
                return "outline";
        }
    }
</script>

<Sidebar.Group>
    <Sidebar.GroupLabel>My Bookings</Sidebar.GroupLabel>
    <Sidebar.GroupContent>
        {#if loading}
            <div class="text-muted-foreground px-3 py-2 text-xs">
                Loading…
            </div>
        {:else if bookings.length === 0}
            <div class="text-muted-foreground px-3 py-2 text-xs">
                No bookings yet.
            </div>
        {:else}
            <Sidebar.Menu>
                {#each bookings as b (b.id)}
                    <Sidebar.MenuItem>
                        <Sidebar.MenuButton
                            onclick={() => goto(`/bookingdetails/${b.id}`)}
                            class="h-auto py-1.5"
                        >
                            <div class="flex w-full flex-col gap-0.5">
                                <div
                                    class="flex items-center justify-between"
                                >
                                    <span class="truncate text-xs font-medium"
                                        >{b.roomName}</span
                                    >
                                    <Badge
                                        variant={badgeVariant(b.status)}
                                        class="h-4 px-1 text-[10px]"
                                    >
                                        {b.status}
                                    </Badge>
                                </div>
                                <span
                                    class="text-muted-foreground text-[10px]"
                                >
                                    {b.date} · {b.slotCount} slot{b.slotCount !== 1
                                        ? "s"
                                        : ""}
                                </span>
                            </div>
                        </Sidebar.MenuButton>
                        <DropdownMenu.Root>
                            <DropdownMenu.Trigger>
                                {#snippet child({ props })}
                                    <Sidebar.MenuAction {...props}>
                                        <EllipsisIcon class="size-3.5" />
                                        <span class="sr-only">Actions</span>
                                    </Sidebar.MenuAction>
                                {/snippet}
                            </DropdownMenu.Trigger>
                            <DropdownMenu.Content
                                align="start"
                                side="right"
                            >
                                <DropdownMenu.Item
                                    onclick={() =>
                                        goto(`/bookingdetails/${b.id}`)}
                                >
                                    View details
                                </DropdownMenu.Item>
                                <DropdownMenu.Item
                                    onclick={() => goto("/bookings")}
                                >
                                    All bookings
                                </DropdownMenu.Item>
                            </DropdownMenu.Content>
                        </DropdownMenu.Root>
                    </Sidebar.MenuItem>
                {/each}
            </Sidebar.Menu>
        {/if}
    </Sidebar.GroupContent>
</Sidebar.Group>
