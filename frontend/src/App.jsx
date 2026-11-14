import { useState } from "react";
import CycleCalendar from "./components/CycleCalendar";

import HabitsForm from "./components/HabitsForm";
import ProfileResult from "./components/ProfileResult";
import ExplanationPanel from "./components/ExplanationPanel";

import { emptyForm, example } from "./config/profileConfig";
import {
  getProfile,
  getExplanation,
  errorMessage,
} from "./services/api";

export default function App() {
  const [form, setForm] = useState({ ...emptyForm });
  const [profile, setProfile] = useState(null);
  const [submitted, setSubmitted] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [usingExample, setUsingExample] = useState(false);

  function clearResults() {
    setProfile(null);
    setSubmitted(null);
    setExplanation(null);
    setError("");
  }

  function changeField(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
    setUsingExample(false);
    clearResults();
  }

  function useExample() {
    setForm({ ...example });
    setUsingExample(true);
    clearResults();
  }

  async function analyze(event) {
    event.preventDefault();
    if (busy) return;

    clearResults();
    setBusy("profile");

    const payload = Object.fromEntries(
      Object.entries(form).map(([key, value]) => [
        key,
        Number(value),
      ])
    );

    try {
      const result = await getProfile(payload);
      setProfile(result);
      setSubmitted(payload);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy("");
    }
  }

  async function explain() {
    if (!submitted || !profile || busy) return;

    setBusy("explanation");
    setError("");
    setExplanation(null);

    try {
      const result = await getExplanation(submitted);

      if (result.profile_id !== profile.profile_id) {
        throw new Error(
          "The profile changed between requests. Please analyze again."
        );
      }

      setExplanation(result);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy("");
    }
  }

  return (
    <>
      <header>
        <h1>Luna Fit</h1>
        <p>Understand your nutrition and activity patterns.</p>
      </header>

      <main>
  <CycleCalendar />

  <HabitsForm
    form={form}
    busy={busy}
    usingExample={usingExample}
    onChange={changeField}
    onUseExample={useExample}
    onSubmit={analyze}
  />

  {error && <p role="alert">{error}</p>}
      
      

        <ProfileResult
          profile={profile}
          busy={busy}
          onExplain={explain}
        />

        <ExplanationPanel
          explanation={explanation}
          busy={busy}
        />
      </main>

      <footer>
        <p>
          Exploratory NHANES-based profiles—not diagnoses, personal
          nutrient requirements, or menstrual-phase predictions.
        </p>
      </footer>
    </>
  );
}