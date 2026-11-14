import { groups } from "../config/profileConfig";

export default function HabitsForm({
  form,
  busy,
  usingExample,
  onChange,
  onUseExample,
  onSubmit,
}) {
  return (
    <section id="habits">
      <h2>Your reported habits</h2>

      <button
        type="button"
        onClick={onUseExample}
        disabled={Boolean(busy)}
      >
        Use example
      </button>

      {usingExample && (
        <p>
          Example mode: these are synthetic values, not your personal data.
        </p>
      )}

      <form onSubmit={onSubmit}>
        <fieldset disabled={Boolean(busy)}>
          <legend>Nutrition and activity inputs</legend>

          {groups.map((group) => (
            <section key={group.title}>
              <h3>{group.title}</h3>
              <p>{group.hint}</p>

              {group.fields.map(
                ([key, label, unit, min, max, step]) => (
                  <div key={key}>
                    <label htmlFor={key}>
                      {label} ({unit})
                    </label>

                    <input
                      id={key}
                      name={key}
                      type="number"
                      min={min}
                      max={max}
                      step={step}
                      required
                      value={form[key]}
                      onChange={(event) =>
                        onChange(key, event.target.value)
                      }
                    />
                  </div>
                )
              )}
            </section>
          ))}

          <button type="submit">
            {busy === "profile"
              ? "Finding your profile…"
              : "Explore my profile"}
          </button>
        </fieldset>
      </form>

      <p>
        These endpoints do not save your submitted habits to the application
        database. Explanations use your local Ollama service.
      </p>
    </section>
  );
}