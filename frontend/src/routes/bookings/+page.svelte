<script lang="ts">
    import {
        type ColumnDef,
        type ColumnFiltersState,
        type PaginationState,
        type SortingState,
        type VisibilityState,
        getCoreRowModel,
        getFilteredRowModel,
        getPaginationRowModel,
        getSortedRowModel,
    } from "@tanstack/table-core";
    import { createRawSnippet } from "svelte";
    import {
        FlexRender,
        createSvelteTable,
        renderComponent,
        renderSnippet,
    } from "$lib/components/ui/data-table/index.js";
    import * as Table from "$lib/components/ui/table/index.js";
    import { Button } from "$lib/components/ui/button/index.js";
    import { Input } from "$lib/components/ui/input/index.js";
    import { Badge } from "$lib/components/ui/badge/index.js";
    import { Separator } from "$lib/components/ui/separator/index.js";
    import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
    import ChevronDownIcon from "@lucide/svelte/icons/chevron-down";
    import SortButton from "$lib/components/room-table/sort-button.svelte";
    import BookingActions from "$lib/components/booking-table/actions.svelte";
    import { apiFetch } from "$lib/api";

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

    /** Flattened row for the data table */
    interface BookingRow {
        id: number;
        roomName: string;
        roomId: number;
        status: string;
        date: string;
        slots: string;
        slotCount: number;
        recurrence: string;
        createdAt: string;
    }

    // ── State ────────────────────────────────────────────────────
    let loading = $state(true);
    let error = $state("");
    let bookingRows = $state<BookingRow[]>([]);

    // ── Load data ────────────────────────────────────────────────
    $effect(() => {
        loadBookings();
    });

    async function loadBookings() {
        loading = true;
        error = "";
        try {
            const bookings = await apiFetch<BookingResponse[]>("/api/bookings");

            // Gather unique room IDs and fetch their names
            const roomIds = [...new Set(bookings.map((b) => b.roomID))];
            const roomMap = new Map<number, string>();
            await Promise.all(
                roomIds.map(async (rid) => {
                    try {
                        const room = await apiFetch<RoomBasic>(
                            `/api/rooms/${rid}`,
                        );
                        roomMap.set(rid, room.name);
                    } catch {
                        roomMap.set(rid, `Room #${rid}`);
                    }
                }),
            );

            bookingRows = bookings.map((b) => {
                const firstSlot = b.timeSlots[0];
                const slotDate = firstSlot?.slot_date ?? "—";
                const slots = b.timeSlots
                    .map(
                        (s) =>
                            `${s.start_time.slice(0, 5)}–${s.end_time.slice(0, 5)}`,
                    )
                    .join(", ");
                return {
                    id: b.id,
                    roomName: roomMap.get(b.roomID) ?? `Room #${b.roomID}`,
                    roomId: b.roomID,
                    status: b.status,
                    date: slotDate,
                    slots,
                    slotCount: b.timeSlots.length,
                    recurrence: b.recurrenceFrequency,
                    createdAt: new Date(b.createdAt).toLocaleDateString(),
                };
            });
        } catch (e) {
            error = e instanceof Error ? e.message : "Failed to load bookings.";
        } finally {
            loading = false;
        }
    }

    // ── Status badge variant ─────────────────────────────────────
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

    // ── Column definitions ───────────────────────────────────────
    const columns: ColumnDef<BookingRow>[] = [
        {
            accessorKey: "roomName",
            header: ({ column }) =>
                renderComponent(SortButton, {
                    label: "Room",
                    onclick: column.getToggleSortingHandler(),
                }),
            cell: ({ row }) => {
                const s = createRawSnippet<[{ name: string }]>((getName) => {
                    const { name } = getName();
                    return {
                        render: () =>
                            `<span class="font-medium">${name}</span>`,
                    };
                });
                return renderSnippet(s, { name: row.original.roomName });
            },
        },
        {
            accessorKey: "status",
            header: "Status",
            cell: ({ row }) =>
                renderComponent(Badge, {
                    variant: statusVariant(row.original.status),
                    children: createRawSnippet(() => ({
                        render: () =>
                            `<span class="capitalize">${row.original.status}</span>`,
                    })),
                }),
        },
        {
            accessorKey: "date",
            header: ({ column }) =>
                renderComponent(SortButton, {
                    label: "Date",
                    onclick: column.getToggleSortingHandler(),
                }),
        },
        {
            accessorKey: "slotCount",
            header: "Slots",
            cell: ({ row }) => {
                const s = createRawSnippet<[{ count: number }]>((getCount) => {
                    const { count } = getCount();
                    return {
                        render: () =>
                            `<span class="text-muted-foreground">${count} slot${count !== 1 ? "s" : ""}</span>`,
                    };
                });
                return renderSnippet(s, { count: row.original.slotCount });
            },
        },
        {
            accessorKey: "slots",
            header: "Time Slots",
            cell: ({ row }) => {
                const s = createRawSnippet<[{ slots: string }]>((getSlots) => {
                    const { slots } = getSlots();
                    return {
                        render: () =>
                            `<span class="text-muted-foreground text-xs">${slots || "—"}</span>`,
                    };
                });
                return renderSnippet(s, { slots: row.original.slots });
            },
            enableSorting: false,
        },
        {
            accessorKey: "recurrence",
            header: "Recurrence",
            cell: ({ row }) => {
                const s = createRawSnippet<[{ recurrence: string }]>(
                    (getRec) => {
                        const { recurrence } = getRec();
                        return {
                            render: () =>
                                `<span class="text-muted-foreground capitalize">${recurrence}</span>`,
                        };
                    },
                );
                return renderSnippet(s, {
                    recurrence: row.original.recurrence,
                });
            },
        },
        {
            accessorKey: "createdAt",
            header: ({ column }) =>
                renderComponent(SortButton, {
                    label: "Submitted",
                    onclick: column.getToggleSortingHandler(),
                }),
            cell: ({ row }) => {
                const s = createRawSnippet<[{ date: string }]>((getDate) => {
                    const { date } = getDate();
                    return {
                        render: () =>
                            `<span class="text-muted-foreground text-xs">${date}</span>`,
                    };
                });
                return renderSnippet(s, { date: row.original.createdAt });
            },
        },
        {
            id: "actions",
            enableHiding: false,
            enableSorting: false,
            cell: ({ row }) =>
                renderComponent(BookingActions, {
                    bookingId: row.original.id,
                    roomName: row.original.roomName,
                }),
        },
    ];

    // ── Table state ──────────────────────────────────────────────
    let pagination = $state<PaginationState>({ pageIndex: 0, pageSize: 10 });
    let sorting = $state<SortingState>([]);
    let columnFilters = $state<ColumnFiltersState>([]);
    let columnVisibility = $state<VisibilityState>({});

    const table = createSvelteTable({
        get data() {
            return bookingRows;
        },
        columns,
        state: {
            get pagination() {
                return pagination;
            },
            get sorting() {
                return sorting;
            },
            get columnVisibility() {
                return columnVisibility;
            },
            get columnFilters() {
                return columnFilters;
            },
        },
        getCoreRowModel: getCoreRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getFilteredRowModel: getFilteredRowModel(),
        onPaginationChange: (updater) => {
            if (typeof updater === "function") {
                pagination = updater(pagination);
            } else {
                pagination = updater;
            }
        },
        onSortingChange: (updater) => {
            if (typeof updater === "function") {
                sorting = updater(sorting);
            } else {
                sorting = updater;
            }
        },
        onColumnFiltersChange: (updater) => {
            if (typeof updater === "function") {
                columnFilters = updater(columnFilters);
            } else {
                columnFilters = updater;
            }
        },
        onColumnVisibilityChange: (updater) => {
            if (typeof updater === "function") {
                columnVisibility = updater(columnVisibility);
            } else {
                columnVisibility = updater;
            }
        },
    });
</script>

<div class="flex flex-1 flex-col gap-6 p-6">
    <div>
        <h1 class="text-2xl font-semibold tracking-tight">Bookings</h1>
        <p class="text-muted-foreground text-sm">
            View and manage your room bookings.
        </p>
    </div>

    <Separator />

    {#if loading}
        <div
            class="text-muted-foreground flex flex-1 items-center justify-center text-sm"
        >
            Loading bookings…
        </div>
    {:else if error}
        <div
            class="text-muted-foreground flex flex-1 items-center justify-center text-sm"
        >
            {error}
        </div>
    {:else}
        <div class="w-full">
            <div class="flex items-center gap-2 pb-4">
                <Input
                    placeholder="Filter by room..."
                    value={(table
                        .getColumn("roomName")
                        ?.getFilterValue() as string) ?? ""}
                    oninput={(e) =>
                        table
                            .getColumn("roomName")
                            ?.setFilterValue(e.currentTarget.value)}
                    class="max-w-sm"
                />
                <DropdownMenu.Root>
                    <DropdownMenu.Trigger>
                        {#snippet child({ props })}
                            <Button
                                {...props}
                                variant="outline"
                                class="ms-auto"
                            >
                                Columns
                                <ChevronDownIcon class="ms-2 size-4" />
                            </Button>
                        {/snippet}
                    </DropdownMenu.Trigger>
                    <DropdownMenu.Content align="end">
                        {#each table
                            .getAllColumns()
                            .filter( (col) => col.getCanHide(), ) as column (column.id)}
                            <DropdownMenu.CheckboxItem
                                class="capitalize"
                                bind:checked={
                                    () => column.getIsVisible(),
                                    (v) => column.toggleVisibility(!!v)
                                }
                            >
                                {column.id}
                            </DropdownMenu.CheckboxItem>
                        {/each}
                    </DropdownMenu.Content>
                </DropdownMenu.Root>
            </div>
            <div class="rounded-md border">
                <Table.Root>
                    <Table.Header>
                        {#each table.getHeaderGroups() as headerGroup (headerGroup.id)}
                            <Table.Row>
                                {#each headerGroup.headers as header (header.id)}
                                    <Table.Head>
                                        {#if !header.isPlaceholder}
                                            <FlexRender
                                                content={header.column.columnDef
                                                    .header}
                                                context={header.getContext()}
                                            />
                                        {/if}
                                    </Table.Head>
                                {/each}
                            </Table.Row>
                        {/each}
                    </Table.Header>
                    <Table.Body>
                        {#each table.getRowModel().rows as row (row.id)}
                            <Table.Row>
                                {#each row.getVisibleCells() as cell (cell.id)}
                                    <Table.Cell>
                                        <FlexRender
                                            content={cell.column.columnDef.cell}
                                            context={cell.getContext()}
                                        />
                                    </Table.Cell>
                                {/each}
                            </Table.Row>
                        {:else}
                            <Table.Row>
                                <Table.Cell
                                    colspan={columns.length}
                                    class="h-24 text-center"
                                >
                                    No bookings found.
                                </Table.Cell>
                            </Table.Row>
                        {/each}
                    </Table.Body>
                </Table.Root>
            </div>
            <div class="flex items-center justify-end space-x-2 pt-4">
                <div class="text-muted-foreground flex-1 text-sm">
                    {table.getFilteredRowModel().rows.length} booking(s)
                </div>
                <div class="space-x-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onclick={() => table.previousPage()}
                        disabled={!table.getCanPreviousPage()}
                    >
                        Previous
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        onclick={() => table.nextPage()}
                        disabled={!table.getCanNextPage()}
                    >
                        Next
                    </Button>
                </div>
            </div>
        </div>
    {/if}
</div>
