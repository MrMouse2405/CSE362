/**
 * Dashboard state: tracks the selected calendar date, fetched rooms,
 * and which dates in the current month have available rooms.
 */

import { apiFetch } from "$lib/api";

export interface TimeSlotRead {
  id: number;
  room_id: number;
  slot_date: string;
  start_time: string;
  end_time: string;
  status: "available" | "held" | "booked";
}

export interface RoomRead {
  id: number;
  name: string;
  capacity: number;
  time_slots: TimeSlotRead[];
}

class DashboardState {
  /** ISO date string of the currently selected day (e.g. "2026-03-16") */
  #selectedDate = $state<string | null>(null);

  /** Rooms (with time slots) for the selected date */
  #rooms = $state<RoomRead[]>([]);

  /** Set of ISO date strings that have available rooms in the visible month */
  #availableDates = $state<Set<string>>(new Set());

  /** True while rooms are being fetched */
  #loadingRooms = $state(false);

  /** True while available dates are being fetched */
  #loadingDates = $state(false);

  get selectedDate() {
    return this.#selectedDate;
  }

  get rooms() {
    return this.#rooms;
  }

  get availableDates() {
    return this.#availableDates;
  }

  get loadingRooms() {
    return this.#loadingRooms;
  }

  get loadingDates() {
    return this.#loadingDates;
  }

  /** Check if a given ISO date string has available rooms */
  isDateAvailable(isoDate: string): boolean {
    return this.#availableDates.has(isoDate);
  }

  /** Select a date and fetch rooms for it */
  async selectDate(isoDate: string) {
    this.#selectedDate = isoDate;
    this.#loadingRooms = true;
    try {
      this.#rooms = await apiFetch<RoomRead[]>(`/api/rooms?date=${isoDate}`);
    } catch {
      this.#rooms = [];
    } finally {
      this.#loadingRooms = false;
    }
  }

  /** Fetch which dates in a given year/month have available rooms */
  async loadAvailableDates(year: number, month: number) {
    this.#loadingDates = true;
    try {
      const dates = await apiFetch<string[]>(
        `/api/rooms/dates?year=${year}&month=${month}`,
      );
      this.#availableDates = new Set(dates);
    } catch {
      this.#availableDates = new Set();
    } finally {
      this.#loadingDates = false;
    }
  }
}

export const dashboard = new DashboardState();
