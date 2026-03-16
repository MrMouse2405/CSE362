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
    import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
    import ChevronDownIcon from "@lucide/svelte/icons/chevron-down";
    import SortButton from "./room-table/sort-button.svelte";
    import Actions from "./room-table/actions.svelte";
    import {
        dashboard,
        type RoomRead,
    } from "$lib/state/dashboard.svelte";

    /** Flattened row type for the table */
    type RoomRow = {
        id: number;
        name: string;
        capacity: number;
        available: number;
        held: number;
        booked: number;
        slots: string;
    };

    /** Derive table data from dashboard state — only rooms with available slots */
    const tableData = $derived<RoomRow[]>(
        dashboard.rooms
            .map((room) => {
                const available = room.time_slots.filter(
                    (s) => s.status === "available",
                ).length;
                const held = room.time_slots.filter(
                    (s) => s.status === "held",
                ).length;
                const booked = room.time_slots.filter(
                    (s) => s.status === "booked",
                ).length;
                const slots = room.time_slots
                    .filter((s) => s.status === "available")
                    .map(
                        (s) =>
                            `${s.start_time.slice(0, 5)}–${s.end_time.slice(0, 5)}`,
                    )
                    .join(", ");
                return { id: room.id, name: room.name, capacity: room.capacity, available, held, booked, slots };
            })
            .filter((r) => r.available > 0),
    );

    const columns: ColumnDef<RoomRow>[] = [
        {
            accessorKey: "name",
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
                return renderSnippet(s, { name: row.original.name });
            },
        },
        {
            accessorKey: "capacity",
            header: ({ column }) =>
                renderComponent(SortButton, {
                    label: "Capacity",
                    onclick: column.getToggleSortingHandler(),
                }),
            cell: ({ row }) => {
                const s = createRawSnippet<[{ capacity: number }]>(
                    (getCap) => {
                        const { capacity } = getCap();
                        return {
                            render: () =>
                                `<span class="text-muted-foreground">${capacity}</span>`,
                        };
                    },
                );
                return renderSnippet(s, { capacity: row.original.capacity });
            },
        },
        {
            accessorKey: "available",
            header: ({ column }) =>
                renderComponent(SortButton, {
                    label: "Available",
                    onclick: column.getToggleSortingHandler(),
                }),
            cell: ({ row }) =>
                renderComponent(Badge, {
                    variant: "default",
                    children: createRawSnippet(() => ({
                        render: () => `${row.original.available} slots`,
                    })),
                }),
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
            id: "actions",
            enableHiding: false,
            enableSorting: false,
            cell: ({ row }) =>
                renderComponent(Actions, {
                    roomId: row.original.id,
                    roomName: row.original.name,
                }),
        },
    ];

    let pagination = $state<PaginationState>({ pageIndex: 0, pageSize: 10 });
    let sorting = $state<SortingState>([]);
    let columnFilters = $state<ColumnFiltersState>([]);
    let columnVisibility = $state<VisibilityState>({});

    const table = createSvelteTable({
        get data() {
            return tableData;
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

{#if !dashboard.selectedDate}
    <div
        class="text-muted-foreground flex flex-1 items-center justify-center p-8 text-sm"
    >
        Select a date from the calendar to view available rooms.
    </div>
{:else if dashboard.loadingRooms}
    <div
        class="text-muted-foreground flex flex-1 items-center justify-center p-8 text-sm"
    >
        Loading rooms…
    </div>
{:else}
    <div class="w-full p-4">
        <div class="flex items-center gap-2 py-4">
            <Input
                placeholder="Filter rooms..."
                value={(table.getColumn("name")?.getFilterValue() as string) ??
                    ""}
                oninput={(e) =>
                    table
                        .getColumn("name")
                        ?.setFilterValue(e.currentTarget.value)}
                class="max-w-sm"
            />
            <DropdownMenu.Root>
                <DropdownMenu.Trigger>
                    {#snippet child({ props })}
                        <Button {...props} variant="outline" class="ms-auto">
                            Columns <ChevronDownIcon class="ms-2 size-4" />
                        </Button>
                    {/snippet}
                </DropdownMenu.Trigger>
                <DropdownMenu.Content align="end">
                    {#each table
                        .getAllColumns()
                        .filter((col) => col.getCanHide()) as column (column.id)}
                        <DropdownMenu.CheckboxItem
                            class="capitalize"
                            bind:checked={() => column.getIsVisible(), (v) => column.toggleVisibility(!!v)}
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
                                No rooms with available slots on {dashboard.selectedDate}.
                            </Table.Cell>
                        </Table.Row>
                    {/each}
                </Table.Body>
            </Table.Root>
        </div>
        <div class="flex items-center justify-end space-x-2 pt-4">
            <div class="text-muted-foreground flex-1 text-sm">
                {table.getFilteredRowModel().rows.length} room(s) available
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
