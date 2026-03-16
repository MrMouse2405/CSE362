<script lang="ts">
    import { Calendar } from "$lib/components/ui/calendar/index.js";
    import * as Sidebar from "$lib/components/ui/sidebar/index.js";
    import { Calendar as CalendarPrimitive } from "bits-ui";
    import {
        CalendarDate,
        today,
        getLocalTimeZone,
        type DateValue,
    } from "@internationalized/date";
    import { dashboard } from "$lib/state/dashboard.svelte";
    import { cn } from "$lib/utils.js";
    import { buttonVariants } from "$lib/components/ui/button/index.js";

    let value = $state<DateValue | undefined>(undefined);
    let placeholder = $state<DateValue>(today(getLocalTimeZone()));

    // Load available dates for the initial month on mount
    $effect(() => {
        dashboard.loadAvailableDates(placeholder.year, placeholder.month);
    });

    function handleValueChange(newValue: DateValue | undefined) {
        value = newValue;
        if (newValue) {
            const iso = `${String(newValue.year).padStart(4, "0")}-${String(newValue.month).padStart(2, "0")}-${String(newValue.day).padStart(2, "0")}`;
            dashboard.selectDate(iso);
        }
    }

    function handlePlaceholderChange(newPlaceholder: DateValue) {
        placeholder = newPlaceholder;
        dashboard.loadAvailableDates(newPlaceholder.year, newPlaceholder.month);
    }

    function toIso(d: DateValue): string {
        return `${String(d.year).padStart(4, "0")}-${String(d.month).padStart(2, "0")}-${String(d.day).padStart(2, "0")}`;
    }
</script>

<Sidebar.Group class="px-0">
    <Sidebar.GroupContent>
        <Calendar
            type="single"
            {value}
            onValueChange={handleValueChange}
            {placeholder}
            onPlaceholderChange={handlePlaceholderChange}
            class=":data-bits-calendar-head-cell:w-[33px] **:role=gridcell:w-[33px] select-none"
        >
            {#snippet day({ day: d, outsideMonth })}
                {@const iso = toIso(d)}
                {@const hasRooms = dashboard.isDateAvailable(iso)}
                <CalendarPrimitive.Day
                    class={cn(
                        buttonVariants({ variant: "ghost" }),
                        "flex size-(--cell-size) flex-col items-center justify-center gap-0.5 p-0 leading-none font-normal whitespace-nowrap select-none",
                        "[&[data-today]:not([data-selected])]:bg-accent [&[data-today]:not([data-selected])]:text-accent-foreground",
                        "data-selected:bg-primary data-selected:text-primary-foreground",
                        "[&[data-outside-month]:not([data-selected])]:text-muted-foreground",
                        "data-disabled:text-muted-foreground data-disabled:pointer-events-none data-disabled:opacity-50",
                        "data-unavailable:text-muted-foreground data-unavailable:line-through",
                        "focus:border-ring focus:ring-ring/50 focus:relative",
                        outsideMonth && "text-muted-foreground opacity-50",
                    )}
                >
                    {d.day}
                    <span
                        class={cn(
                            "size-1 rounded-full",
                            hasRooms && !outsideMonth
                                ? "bg-primary"
                                : "bg-transparent",
                        )}
                    ></span>
                </CalendarPrimitive.Day>
            {/snippet}
        </Calendar>
    </Sidebar.GroupContent>
</Sidebar.Group>
