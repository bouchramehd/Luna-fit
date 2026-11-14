export const groups = [
  {
    title: "About you",
    hint: "Adults only. Age provides context; it does not determine your profile.",
    fields: [
      ["age", "Age", "years", 18, 120, "1"],
    ],
  },
  {
    title: "One day of dietary intake",
    hint: "Enter reported intake, not calorie or nutrient targets.",
    fields: [
      ["energy_kcal", "Energy", "kcal/day", 1, undefined, "any"],
      ["protein_g", "Protein", "g/day", 0, undefined, "any"],
      ["carbohydrate_g", "Carbohydrates", "g/day", 0, undefined, "any"],
      ["fat_g", "Fat", "g/day", 0, undefined, "any"],
      ["iron_mg", "Iron", "mg/day", 0, undefined, "any"],
    ],
  },
  {
    title: "Your typical activity",
    hint:
      "Recreation and transport: minutes per typical week. " +
      "Sitting: minutes per typical day, excluding sleep. " +
      "Enter 0 only when you report none.",
    fields: [
      [
        "vigorous_recreation_minutes_week",
        "Vigorous recreation",
        "min/week", 0, 10079, "any",
      ],
      [
        "moderate_recreation_minutes_week",
        "Moderate recreation",
        "min/week", 0, 10079, "any",
      ],
      [
        "active_transport_minutes_week",
        "Walking or cycling for transport",
        "min/week", 0, 10079, "any",
      ],
      [
        "sedentary_minutes_day",
        "Time sitting",
        "min/day", 0, 1439, "any",
      ],
    ],
  },
];

export const emptyForm = Object.fromEntries(
  groups.flatMap((group) =>
    group.fields.map(([key]) => [key, ""])
  )
);

// Synthetic demonstration values, not personal user data.
export const example = {
  age: 25,
  energy_kcal: 2000,
  protein_g: 80,
  carbohydrate_g: 250,
  fat_g: 75,
  iron_mg: 14,
  vigorous_recreation_minutes_week: 90,
  moderate_recreation_minutes_week: 150,
  active_transport_minutes_week: 60,
  sedentary_minutes_day: 420,
};

// Descriptions apply only to the saved k=4 model.
// They summarize observed validation-group patterns, not health rankings.
export const descriptions = {
  0: {
    name: "Recreational activity pattern",
    text:
      "This group showed more reported vigorous and moderate " +
      "recreational activity than the other groups.",
  },
  1: {
    name: "Active transport pattern",
    text:
      "This group showed more reported walking or cycling " +
      "for transport than the other groups.",
  },
  2: {
    name: "Higher fat-density pattern",
    text:
      "This group had higher median fat intake per 1,000 kcal. " +
      "Median reported recreational and transport activity was zero.",
  },
  3: {
    name: "Higher carbohydrate-density pattern",
    text:
      "This group had higher median carbohydrate and iron intake " +
      "per 1,000 kcal. Median reported recreational and transport " +
      "activity was zero.",
  },
};