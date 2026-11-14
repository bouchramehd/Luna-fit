import { useState } from "react";

const DAY = 86400000;
const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function todayKey() {
  const date = new Date();
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, "0"),
    String(date.getDate()).padStart(2, "0"),
  ].join("-");
}

function dayNumber(key) {
  const [year, month, day] = key.split("-").map(Number);
  return Date.UTC(year, month - 1, day) / DAY;
}

function dateKey(number) {
  return new Date(number * DAY).toISOString().slice(0, 10);
}

function displayDate(key) {
  return new Intl.DateTimeFormat("en", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(dayNumber(key) * DAY));
}

export default function CycleCalendar() {
  const today = todayKey();
  const [month, setMonth] = useState(() => {
    const now = new Date();
    return { year: now.getFullYear(), month: now.getMonth() };
  });
  const [selected, setSelected] = useState(today);
  const [entry, setEntry] = useState(null);
  const [draft, setDraft] = useState({
    start: "",
    cycleLength: 28,
    periodLength: 5,
  });
  const [notice, setNotice] = useState("");

  const firstDay = new Date(
    Date.UTC(month.year, month.month, 1)
  );
  const firstNumber = firstDay.getTime() / DAY;
  const mondayOffset = (firstDay.getUTCDay() + 6) % 7;
  const gridStart = firstNumber - mondayOffset;

  const monthLabel = new Intl.DateTimeFormat("en", {
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(firstDay);

  const startNumber = entry ? dayNumber(entry.start) : null;
  const nextStart = entry ? startNumber + entry.cycleLength : null;
  const daysUntil = entry ? nextStart - dayNumber(today) : null;
  const elapsed = entry ? dayNumber(today) - startNumber : null;

  function changeMonth(offset) {
    const next = new Date(
      Date.UTC(month.year, month.month + offset, 1)
    );
    setMonth({
      year: next.getUTCFullYear(),
      month: next.getUTCMonth(),
    });
  }

  function selectDay(key) {
    setSelected(key);
    setNotice("");

    if (key <= today) {
      setDraft((current) => ({ ...current, start: key }));
    }
  }

  function saveEntry(event) {
    event.preventDefault();

    const cycleLength = Number(draft.cycleLength);
    const periodLength = Number(draft.periodLength);

    if (
      !draft.start ||
      draft.start > today ||
      !Number.isInteger(cycleLength) ||
      cycleLength < 20 ||
      cycleLength > 45 ||
      !Number.isInteger(periodLength) ||
      periodLength < 1 ||
      periodLength > 10 ||
      periodLength > cycleLength
    ) {
      setNotice("Check the start date and cycle durations.");
      return;
    }

    setEntry({
      start: draft.start,
      cycleLength,
      periodLength,
    });
    setSelected(draft.start);

    const date = new Date(dayNumber(draft.start) * DAY);
    setMonth({
      year: date.getUTCFullYear(),
      month: date.getUTCMonth(),
    });

    setNotice("Period start logged for this session.");
  }

  function selectedDescription() {
    if (!entry) return "Choose a date to log your period start.";

    const number = dayNumber(selected);

    if (number === startNumber) {
      return "Your logged period-start date.";
    }
    if (
      number > startNumber &&
      number < startNumber + entry.periodLength
    ) {
      return "Period window estimated from your usual duration.";
    }
    if (
      number >= nextStart &&
      number < nextStart + entry.periodLength
    ) {
      return "Estimated next period window—not a confirmed date.";
    }

    return "No period entry recorded for this date.";
  }

  return (
    <section
      id="cycle-calendar"
      className="overflow-hidden rounded-3xl border border-rose-100 bg-white"
    >
      <div className="mb-7 flex flex-wrap items-start justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-[0.2em] text-rose-500">
            YOUR CYCLE · YOUR CHECK-IN
          </span>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-800">
            A little closer to your rhythm
          </h2>
          <p className="max-w-xl text-sm text-slate-500">
            Log your period start and explore calendar estimates based
            on the cycle length you enter.
          </p>
        </div>

        <span className="rounded-full bg-rose-50 px-4 py-2 text-xs font-semibold text-rose-700">
          Session only · not saved to your account yet
        </span>
      </div>

      <div className="grid gap-8 lg:grid-cols-[1.3fr_1fr]">
        <div>
          <div className="mb-5 flex items-center justify-between">
            <button
              type="button"
              aria-label="Previous month"
              onClick={() => changeMonth(-1)}
              className="m-0 flex h-10 w-10 items-center justify-center rounded-full bg-rose-50 p-0 text-xl text-rose-700 hover:bg-rose-100"
            >
              ‹
            </button>

            <h3 className="text-lg font-semibold text-slate-800">
              {monthLabel}
            </h3>

            <button
              type="button"
              aria-label="Next month"
              onClick={() => changeMonth(1)}
              className="m-0 flex h-10 w-10 items-center justify-center rounded-full bg-rose-50 p-0 text-xl text-rose-700 hover:bg-rose-100"
            >
              ›
            </button>
          </div>

          <div className="grid grid-cols-7 text-center">
            {WEEKDAYS.map((day) => (
              <div
                key={day}
                className="pb-3 text-xs font-semibold text-slate-400"
              >
                {day}
              </div>
            ))}

            {Array.from({ length: 42 }, (_, index) => {
              const number = gridStart + index;
              const key = dateKey(number);
              const date = new Date(number * DAY);
              const outside = date.getUTCMonth() !== month.month;
              const isStart = entry && number === startNumber;
              const periodWindow =
                entry &&
                number > startNumber &&
                number < startNumber + entry.periodLength;
              const predicted =
                entry &&
                number >= nextStart &&
                number < nextStart + entry.periodLength;

              let color = outside
                ? "bg-transparent text-slate-300"
                : "bg-transparent text-slate-700";

              if (periodWindow) color = "bg-rose-100 text-rose-800";
              if (predicted) {
                color = "border-2 border-dashed border-rose-300 bg-rose-50 text-rose-700";
              }
              if (isStart) color = "bg-rose-500 text-white";

              return (
                <button
                  key={key}
                  type="button"
                  aria-label={`${displayDate(key)}${
                    isStart ? ", logged period start" : ""
                  }${predicted ? ", estimated period" : ""}`}
                  aria-pressed={selected === key}
                  aria-current={key === today ? "date" : undefined}
                  onClick={() => selectDay(key)}
                  className={`relative m-1 flex aspect-square items-center justify-center rounded-full p-0 text-sm transition hover:bg-rose-200 hover:text-rose-900 ${
                    selected === key
                      ? "ring-2 ring-slate-600 ring-offset-2"
                      : ""
                  } ${color}`}
                >
                  {date.getUTCDate()}
                  {key === today && (
                    <span
                      aria-hidden="true"
                      className="absolute bottom-1 h-1 w-1 rounded-full bg-current"
                    />
                  )}
                </button>
              );
            })}
          </div>

          <div className="mt-5 flex flex-wrap gap-4 text-xs text-slate-500">
            <span className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-rose-500" />
              Logged start
            </span>
            <span className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-rose-100" />
              Estimated duration
            </span>
            <span className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full border border-dashed border-rose-400" />
              Estimated next period
            </span>
          </div>

          <div
            className="mt-6 rounded-2xl bg-slate-50 p-4"
            aria-live="polite"
          >
            <strong className="text-sm text-slate-700">
              {displayDate(selected)}
            </strong>
            <p className="text-sm text-slate-500">
              {selectedDescription()}
            </p>
          </div>
        </div>

        <div>
          <div className="rounded-3xl bg-gradient-to-br from-rose-50 to-purple-50 p-6">
            <p className="text-xs font-bold uppercase tracking-widest text-rose-600">
              YOUR NEXT CHECK-IN
            </p>

            <h3 className="mt-3 text-2xl font-bold text-slate-800">
              {!entry
                ? "Start with a date"
                : daysUntil > 0
                  ? `Next period in about ${daysUntil} days`
                  : daysUntil === 0
                    ? "Estimated next start: today"
                    : "Your estimated start date has passed"}
            </h3>

            <p className="text-sm text-slate-600">
              {entry
                ? `Estimated next start: ${displayDate(dateKey(nextStart))}.`
                : "Your dates stay blank until you log a period start."}
            </p>

            {entry && elapsed < entry.cycleLength && (
              <p className="text-sm font-medium text-rose-700">
                Day {elapsed + 1} since your logged start
              </p>
            )}

            {entry && daysUntil < 0 && (
              <p className="text-sm text-slate-600">
                This does not establish that your period is late.
                Log the actual next start when known.
              </p>
            )}
          </div>

          <form onSubmit={saveEntry} className="mt-6">
            <h3 className="text-lg font-semibold text-slate-800">
              Log a period start
            </h3>

            <label htmlFor="period-start">First day of your period</label>
            <input
              id="period-start"
              type="date"
              required
              max={today}
              value={draft.start}
              onChange={(event) =>
                setDraft({ ...draft, start: event.target.value })
              }
            />

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="cycle-length">Usual cycle length</label>
                <input
                  id="cycle-length"
                  type="number"
                  required
                  min="20"
                  max="45"
                  step="1"
                  value={draft.cycleLength}
                  onChange={(event) =>
                    setDraft({ ...draft, cycleLength: event.target.value })
                  }
                />
                <span className="text-xs text-slate-500">days between starts</span>
              </div>

              <div>
                <label htmlFor="period-length">Usual period duration</label>
                <input
                  id="period-length"
                  type="number"
                  required
                  min="1"
                  max="10"
                  step="1"
                  value={draft.periodLength}
                  onChange={(event) =>
                    setDraft({ ...draft, periodLength: event.target.value })
                  }
                />
                <span className="text-xs text-slate-500">days of bleeding</span>
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-rose-500 hover:bg-rose-600"
            >
              Log period start
            </button>

            <p role="status" className="text-sm text-rose-700">
              {notice}
            </p>
          </form>
        </div>
      </div>

      <p className="mt-7 border-t border-rose-100 pt-4 text-xs text-slate-500">
        Calendar estimates can vary, especially with irregular cycles,
        hormonal contraception or postpartum changes. This calendar does
        not confirm ovulation and must not be used for contraception.
        The defaults of 28 and 5 days are editable examples.
      </p>
    </section>
  );
}