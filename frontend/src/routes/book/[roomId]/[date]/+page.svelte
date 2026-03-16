<script lang="ts">
    import { page } from "$app/state";
    import { goto } from "$app/navigation";
    import { apiFetch } from "$lib/api";
    import { Button } from "$lib/components/ui/button/index.js";
    import * as Card from "$lib/components/ui/card/index.js";
    import { Separator } from "$lib/components/ui/separator/index.js";
    import { Badge } from "$lib/components/ui/badge/index.js";
    import { Checkbox } from "$lib/components/ui/checkbox/index.js";
    import {
        DoorOpenIcon,
        UsersIcon,
        ClockIcon,
        CalendarIcon,
        ArrowLeftIcon,
        LoaderCircleIcon,
    } from "@lucide/svelte";

    // ── Route params ─────────────────────────────────────────────
    const roomId = $derived(Number(page.params.roomId));
    const date = $derived(page.params.date); // "2026-03-16"

    // ── Types ────────────────────────────────────────────────────
    interface TimeSlot {
        id: number;
        room_id: number;
        slot_date: string;
        start_time: string;
        end_time: string;
        status: "available" | "held" | "booked";
    }

    interface RoomWithSlots {
        id: number;
        name: string;
        capacity: number;
        time_slots: TimeSlot[];
    }

    // ── State ────────────────────────────────────────────────────
    let room = $state<RoomWithSlots | null>(null);
    let loading = $state(true);
    let submitting = $state(false);
    let error = $state("");
    let success = $state("");
    let selectedSlotIds = $state<Set<number>>(new Set());

    // ── Derived ──────────────────────────────────────────────────
    const availableSlots = $derived(
        room?.time_slots.filter((s) => s.status === "available") ?? [],
    );

    // ── Load room data ───────────────────────────────────────────
    $effect(() => {
        loadRoom();
    });

    async function loadRoom() {
        loading = true;
        error = "";
        try {
            const rooms = await apiFetch<RoomWithSlots[]>(
                `/api/rooms?date=${date}`,
            );
            room = rooms.find((r) => r.id === roomId) ?? null;
            if (!room) {
                error = "Room not found for this date.";
            }
        } catch (e) {
            error = e instanceof Error ? e.message : "Failed to load room.";
        } finally {
            loading = false;
        }
    }

    // ── Slot selection ───────────────────────────────────────────
    function toggleSlot(slotId: number) {
        const next = new Set(selectedSlotIds);
        if (next.has(slotId)) {
            next.delete(slotId);
        } else {
            next.add(slotId);
        }
        selectedSlotIds = next;
    }

    function selectAll() {
        selectedSlotIds = new Set(availableSlots.map((s) => s.id));
    }

    function clearSelection() {
        selectedSlotIds = new Set();
    }

    // ── Submit booking ───────────────────────────────────────────
    async function handleSubmit() {
        if (selectedSlotIds.size === 0) return;
        submitting = true;
        error = "";
        success = "";
        try {
            await apiFetch("/api/bookings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    room_id: roomId,
                    date: date,
                    slot_ids: Array.from(selectedSlotIds),
                    recurrence_freq: "none",
                }),
            });
            success = "Booking submitted successfully! Awaiting approval.";
            selectedSlotIds = new Set();
            // Refresh the room data to reflect held slots
            await loadRoom();
        } catch (e) {
            error = e instanceof Error ? e.message : "Booking failed.";
        } finally {
            submitting = false;
        }
    }
</script>

<div class="flex flex-1 flex-col gap-6 p-6">
    <!-- Back button + heading -->
    <div class="flex items-center gap-4">
        <Button variant="ghost" size="icon" onclick={() => goto("/")}>
            <ArrowLeftIcon class="size-5" />
        </Button>
        <div>
            <h1 class="text-2xl font-semibold tracking-tight">Book a Room</h1>
            <p class="text-muted-foreground text-sm">
                Select time slots and submit your booking request.
            </p>
        </div>
    </div>

    <Separator />

    {#if loading}
        <div
            class="text-muted-foreground flex flex-1 items-center justify-center text-sm"
        >
            Loading room…
        </div>
    {:else if error && !room}
        <div
            class="text-muted-foreground flex flex-1 items-center justify-center text-sm"
        >
            {error}
        </div>
    {:else if room}
        <div class="grid gap-6 lg:grid-cols-3">
            <!-- Room info card -->
            <Card.Root>
                <Card.Header>
                    <Card.Title class="flex items-center gap-2">
                        <DoorOpenIcon class="size-5" />
                        {room.name}
                    </Card.Title>
                    <Card.Description class="flex flex-col gap-1">
                        <span class="flex items-center gap-1.5">
                            <CalendarIcon class="size-3.5" />
                            {date}
                        </span>
                        <span class="flex items-center gap-1.5">
                            <UsersIcon class="size-3.5" />
                            Capacity: {room.capacity}
                        </span>
                    </Card.Description>
                </Card.Header>
                <Card.Content>
                    <div class="flex gap-2">
                        <Badge variant="default">
                            {availableSlots.length} available
                        </Badge>
                        {#if selectedSlotIds.size > 0}
                            <Badge variant="secondary">
                                {selectedSlotIds.size} selected
                            </Badge>
                        {/if}
                    </div>
                </Card.Content>
            </Card.Root>

            <!-- Slot selection -->
            <Card.Root class="lg:col-span-2">
                <Card.Header>
                    <div class="flex items-center justify-between">
                        <Card.Title>Available Time Slots</Card.Title>
                        <div class="flex gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onclick={selectAll}
                                disabled={availableSlots.length === 0}
                            >
                                Select all
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onclick={clearSelection}
                                disabled={selectedSlotIds.size === 0}
                            >
                                Clear
                            </Button>
                        </div>
                    </div>
                </Card.Header>
                <Card.Content>
                    {#if availableSlots.length === 0}
                        <p
                            class="text-muted-foreground py-4 text-center text-sm"
                        >
                            No available slots for this room on {date}.
                        </p>
                    {:else}
                        <div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                            {#each availableSlots as slot (slot.id)}
                                {@const isSelected = selectedSlotIds.has(
                                    slot.id,
                                )}
                                <button
                                    type="button"
                                    class="flex items-center gap-3 rounded-lg border p-3 text-left transition-colors
                                        {isSelected
                                        ? 'border-primary bg-primary/5'
                                        : 'hover:bg-muted/50'}"
                                    onclick={() => toggleSlot(slot.id)}
                                >
                                    <Checkbox
                                        checked={isSelected}
                                        tabindex={-1}
                                    />
                                    <div class="flex items-center gap-2">
                                        <ClockIcon
                                            class="text-muted-foreground size-4"
                                        />
                                        <span class="text-sm font-medium">
                                            {slot.start_time.slice(0, 5)} – {slot.end_time.slice(
                                                0,
                                                5,
                                            )}
                                        </span>
                                    </div>
                                </button>
                            {/each}
                        </div>
                    {/if}
                </Card.Content>
            </Card.Root>
        </div>

        <!-- Submit area -->
        {#if error}
            <div
                class="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-600 dark:border-red-800 dark:bg-red-950 dark:text-red-400"
            >
                {error}
            </div>
        {/if}

        {#if success}
            <div
                class="rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-600 dark:border-green-800 dark:bg-green-950 dark:text-green-400"
            >
                {success}
            </div>
        {/if}

        <div class="flex items-center justify-end gap-3">
            <Button variant="outline" onclick={() => goto("/")}>Cancel</Button>
            <Button
                disabled={selectedSlotIds.size === 0 || submitting}
                onclick={handleSubmit}
            >
                {#if submitting}
                    <LoaderCircleIcon class="mr-2 size-4 animate-spin" />
                    Submitting…
                {:else}
                    Book {selectedSlotIds.size} slot{selectedSlotIds.size !== 1
                        ? "s"
                        : ""}
                {/if}
            </Button>
        </div>
    {/if}
</div>
