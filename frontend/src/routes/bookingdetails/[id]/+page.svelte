<script lang="ts">
    import { page } from "$app/state";
    import { goto } from "$app/navigation";
    import { apiFetch } from "$lib/api";
    import { Button } from "$lib/components/ui/button/index.js";
    import * as Card from "$lib/components/ui/card/index.js";
    import { Badge } from "$lib/components/ui/badge/index.js";
    import { Separator } from "$lib/components/ui/separator/index.js";
    import {
        ArrowLeftIcon,
        DoorOpenIcon,
        CalendarIcon,
        ClockIcon,
        UserIcon,
        RepeatIcon,
    } from "@lucide/svelte";

    // ── Types ────────────────────────────────────────────────────
    interface TimeSlotResponse {
        id: number;
        room_id: number;
        slot_date: string;
        start_time: string;
        end_time: string;
        status: string;
        booking_id: number | null;
    }

    interface BookingResponse {
        id: number;
        userID: string;
        submittedByRole: string;
        roomID: number;
        status: string;
        recurrenceFrequency: string;
        recurrenceEndDate: string | null;
        createdAt: string;
        timeSlots: TimeSlotResponse[];
    }

    interface RoomBasic {
        id: number;
        name: string;
        capacity: number;
    }

    // ── State ────────────────────────────────────────────────────
    const bookingId = $derived(Number(page.params.id));
    let booking = $state<BookingResponse | null>(null);
    let roomName = $state("Loading…");
    let loading = $state(true);
    let error = $state("");

    // ── Load ─────────────────────────────────────────────────────
    $effect(() => {
        loadBooking();
    });

    async function loadBooking() {
        loading = true;
        error = "";
        try {
            const bookings =
                await apiFetch<BookingResponse[]>("/api/bookings");
            booking = bookings.find((b) => b.id === bookingId) ?? null;
            if (!booking) {
                error = "Booking not found.";
                return;
            }
            try {
                const room = await apiFetch<RoomBasic>(
                    `/api/rooms/${booking.roomID}`,
                );
                roomName = room.name;
            } catch {
                roomName = `Room #${booking.roomID}`;
            }
        } catch (e) {
            error = e instanceof Error ? e.message : "Failed to load booking.";
        } finally {
            loading = false;
        }
    }

    function statusVariant(
        status: string,
    ): "default" | "secondary" | "outline" | "destructive" {
        switch (status) {
            case "approved":
                return "default";
            case "pending":
                return "secondary";
            case "denied":
                return "destructive";
            case "cancelled":
                return "outline";
            default:
                return "outline";
        }
    }

    function slotStatusVariant(
        status: string,
    ): "default" | "secondary" | "outline" {
        switch (status) {
            case "booked":
                return "default";
            case "held":
                return "secondary";
            default:
                return "outline";
        }
    }
</script>

<div class="flex flex-1 flex-col gap-6 p-6">
    <!-- Header -->
    <div class="flex items-center gap-4">
        <Button variant="ghost" size="icon" onclick={() => goto("/bookings")}>
            <ArrowLeftIcon class="size-5" />
        </Button>
        <div>
            <h1 class="text-2xl font-semibold tracking-tight">
                Booking Details
            </h1>
            <p class="text-muted-foreground text-sm">
                Booking #{bookingId}
            </p>
        </div>
    </div>

    <Separator />

    {#if loading}
        <div
            class="text-muted-foreground flex flex-1 items-center justify-center text-sm"
        >
            Loading…
        </div>
    {:else if error || !booking}
        <div
            class="text-muted-foreground flex flex-1 items-center justify-center text-sm"
        >
            {error || "Booking not found."}
        </div>
    {:else}
        <div class="grid gap-6 lg:grid-cols-3">
            <!-- Booking info card -->
            <Card.Root>
                <Card.Header>
                    <Card.Title>Booking Info</Card.Title>
                </Card.Header>
                <Card.Content class="grid gap-3">
                    <div class="flex items-center justify-between">
                        <span class="text-muted-foreground text-sm"
                            >Status</span
                        >
                        <Badge variant={statusVariant(booking.status)}>
                            <span class="capitalize">{booking.status}</span>
                        </Badge>
                    </div>
                    <Separator />
                    <div class="flex items-center gap-2">
                        <DoorOpenIcon class="text-muted-foreground size-4" />
                        <span class="text-sm font-medium">{roomName}</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <CalendarIcon class="text-muted-foreground size-4" />
                        <span class="text-sm"
                            >{booking.timeSlots[0]?.slot_date ?? "—"}</span
                        >
                    </div>
                    <div class="flex items-center gap-2">
                        <UserIcon class="text-muted-foreground size-4" />
                        <span class="text-sm capitalize"
                            >{booking.submittedByRole}</span
                        >
                    </div>
                    {#if booking.recurrenceFrequency !== "none"}
                        <div class="flex items-center gap-2">
                            <RepeatIcon
                                class="text-muted-foreground size-4"
                            />
                            <span class="text-sm capitalize">
                                {booking.recurrenceFrequency}
                                {#if booking.recurrenceEndDate}
                                    until {booking.recurrenceEndDate}
                                {/if}
                            </span>
                        </div>
                    {/if}
                    <Separator />
                    <div class="text-muted-foreground text-xs">
                        Submitted: {new Date(
                            booking.createdAt,
                        ).toLocaleString()}
                    </div>
                </Card.Content>
            </Card.Root>

            <!-- Time slots card -->
            <Card.Root class="lg:col-span-2">
                <Card.Header>
                    <Card.Title
                        >Time Slots ({booking.timeSlots.length})</Card.Title
                    >
                </Card.Header>
                <Card.Content>
                    {#if booking.timeSlots.length === 0}
                        <p
                            class="text-muted-foreground py-4 text-center text-sm"
                        >
                            No time slots.
                        </p>
                    {:else}
                        <div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                            {#each booking.timeSlots as slot (slot.id)}
                                <div
                                    class="flex items-center justify-between rounded-lg border p-3"
                                >
                                    <div class="flex items-center gap-2">
                                        <ClockIcon
                                            class="text-muted-foreground size-4"
                                        />
                                        <div>
                                            <span class="text-sm font-medium">
                                                {slot.start_time.slice(0, 5)} – {slot.end_time.slice(
                                                    0,
                                                    5,
                                                )}
                                            </span>
                                            <p
                                                class="text-muted-foreground text-xs"
                                            >
                                                {slot.slot_date}
                                            </p>
                                        </div>
                                    </div>
                                    <Badge
                                        variant={slotStatusVariant(
                                            slot.status,
                                        )}
                                    >
                                        <span class="capitalize"
                                            >{slot.status}</span
                                        >
                                    </Badge>
                                </div>
                            {/each}
                        </div>
                    {/if}
                </Card.Content>
            </Card.Root>
        </div>

        <div class="flex justify-end">
            <Button variant="outline" onclick={() => goto("/bookings")}>
                Back to Bookings
            </Button>
        </div>
    {/if}
</div>
