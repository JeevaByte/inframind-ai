"use client";

import { FormEvent, useState } from "react";
import { AlertTriangle, ExternalLink, Leaf, LoaderCircle, MapPin } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface FieldReadyAlert {
  event: string;
  headline: string;
  effective?: string | null;
  expires?: string | null;
  url: string;
}

interface FieldReadySource {
  title: string;
  url: string;
  retrieved_at: string;
}

interface FieldReadyResult {
  guidance: string;
  actions: string[];
  risk: {
    level: "elevated" | "monitor" | "no_heat_signal" | "unavailable";
    summary: string;
    drought_alert_status: "active_alert" | "no_active_alert_found" | "unavailable";
    forecast_high_f?: number | null;
  };
  alerts_status: "available" | "unavailable";
  forecast_status: "available" | "unavailable";
  active_alerts: FieldReadyAlert[];
  sources: FieldReadySource[];
  limitations: string[];
}

interface ApiEnvelope<T> {
  success: boolean;
  data?: T;
  errors?: string[];
  message?: string;
}

const API_BASE_URL = (
  process.env["NEXT_PUBLIC_ANALYSIS_API_URL"] || "http://localhost:8000"
).replace(/\/$/, "");

const riskLabels: Record<FieldReadyResult["risk"]["level"], string> = {
  elevated: "Elevated screening signal",
  monitor: "Monitor conditions",
  no_heat_signal: "No heat signal found",
  unavailable: "Weather data unavailable",
};

export default function FieldReadyPage() {
  const [latitude, setLatitude] = useState("41.25");
  const [longitude, setLongitude] = useState("-96.00");
  const [crop, setCrop] = useState("corn");
  const [growthStage, setGrowthStage] = useState("vegetative");
  const [result, setResult] = useState<FieldReadyResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function getAdvice(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/fieldready/advice`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          latitude: Number(latitude),
          longitude: Number(longitude),
          crop,
          growth_stage: growthStage,
        }),
      });
      const payload = (await response.json()) as
        | ApiEnvelope<FieldReadyResult>
        | { detail?: string };
      if (!response.ok) {
        throw new Error(
          "detail" in payload
            ? payload.detail || "Could not retrieve field guidance."
            : "Could not retrieve field guidance.",
        );
      }
      if (!("success" in payload) || !payload.success || !payload.data) {
        throw new Error(
          "message" in payload
            ? payload.message || "The response was incomplete."
            : "The response was incomplete.",
        );
      }
      setResult(payload.data);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Something went wrong. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-4xl space-y-8 px-4 py-10 sm:px-6 lg:py-16">
      <header className="space-y-4">
        <Badge variant="outline" className="gap-2 border-primary/30 bg-primary/5 text-primary">
          <Leaf className="h-3.5 w-3.5" /> Climate resilience pilot
        </Badge>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">FieldReady</h1>
        <p className="max-w-2xl text-lg leading-8 text-muted-foreground">
          Get a plain-language weather update and cautious next steps for a corn or soybean field in
          the contiguous United States.
        </p>
        <p className="text-sm text-muted-foreground">
          The National Weather Service and configured Amazon Bedrock model receive your coordinates
          to provide this update. FieldReady does not save them.
        </p>
      </header>

      <Card className="surface-panel rounded-3xl">
        <CardHeader>
          <CardTitle>Field details</CardTitle>
          <CardDescription>Enter decimal coordinates from your map app or device.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={getAdvice} className="grid gap-5 sm:grid-cols-2">
            <label className="space-y-2 text-sm font-medium">
              <span className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-primary" /> Latitude
              </span>
              <Input
                type="number"
                step="any"
                min="24"
                max="50"
                required
                value={latitude}
                onChange={(event) => setLatitude(event.target.value)}
              />
            </label>
            <label className="space-y-2 text-sm font-medium">
              <span className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-primary" /> Longitude
              </span>
              <Input
                type="number"
                step="any"
                min="-125"
                max="-66"
                required
                value={longitude}
                onChange={(event) => setLongitude(event.target.value)}
              />
            </label>
            <label className="space-y-2 text-sm font-medium">
              Crop
              <select
                className="flex h-10 w-full rounded-md border border-slate-200 bg-background px-3 text-sm dark:border-slate-800"
                value={crop}
                onChange={(event) => setCrop(event.target.value)}
              >
                <option value="corn">Corn</option>
                <option value="soybean">Soybean</option>
              </select>
            </label>
            <label className="space-y-2 text-sm font-medium">
              Growth stage
              <select
                className="flex h-10 w-full rounded-md border border-slate-200 bg-background px-3 text-sm dark:border-slate-800"
                value={growthStage}
                onChange={(event) => setGrowthStage(event.target.value)}
              >
                <option value="seedling">Seedling</option>
                <option value="vegetative">Vegetative</option>
                <option value="flowering">Flowering</option>
                <option value="grain_fill">Grain fill</option>
              </select>
            </label>
            <div className="sm:col-span-2">
              <Button type="submit" className="w-full sm:w-auto" disabled={loading}>
                {loading ? (
                  <>
                    <LoaderCircle className="mr-2 h-4 w-4 animate-spin" /> Checking official data…
                  </>
                ) : (
                  "Get field update"
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {error && (
        <Card role="alert" className="border-destructive/50">
          <CardContent className="flex items-start gap-3 p-5 text-sm text-destructive">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <p>{error}</p>
          </CardContent>
        </Card>
      )}

      {result && (
        <section aria-live="polite" className="space-y-5">
          <Card className="surface-panel rounded-3xl">
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <CardTitle>Field update</CardTitle>
                <Badge variant={result.risk.level === "elevated" ? "destructive" : "outline"}>
                  {riskLabels[result.risk.level]}
                </Badge>
              </div>
              <CardDescription>{result.risk.summary}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="whitespace-pre-wrap leading-7">{result.guidance}</div>
              <div>
                <h3 className="mb-2 font-semibold">Suggested follow-up</h3>
                <ul className="list-disc space-y-2 pl-5 text-sm text-muted-foreground">
                  {result.actions.map((action) => (
                    <li key={action}>{action}</li>
                  ))}
                </ul>
              </div>
              <div className="grid gap-3 rounded-xl bg-muted/50 p-4 text-sm sm:grid-cols-2">
                <p>
                  Official alert data: <strong>{result.alerts_status}</strong>
                </p>
                <p>
                  Forecast data: <strong>{result.forecast_status}</strong>
                </p>
                <p>
                  Drought alert:{" "}
                  <strong>{result.risk.drought_alert_status.replaceAll("_", " ")}</strong>
                </p>
                {result.risk.forecast_high_f != null && (
                  <p>
                    Forecast screening high: <strong>{result.risk.forecast_high_f}°F</strong>
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Active NWS alerts</CardTitle>
              <CardDescription>
                {result.alerts_status === "unavailable"
                  ? "Alert data could not be retrieved; this is not confirmation that there are no alerts."
                  : result.active_alerts.length
                    ? "Official alerts returned for these coordinates."
                    : "No active alerts were returned for these coordinates."}
              </CardDescription>
            </CardHeader>
            {result.active_alerts.length > 0 && (
              <CardContent className="space-y-3">
                {result.active_alerts.map((alert, index) => (
                  <a
                    key={`${alert.url}-${index}`}
                    href={alert.url}
                    target="_blank"
                    rel="noreferrer"
                    className="block rounded-xl border p-4 transition-colors hover:bg-muted/50"
                  >
                    <p className="font-semibold">{alert.event}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{alert.headline}</p>
                    {alert.expires && (
                      <p className="mt-2 text-xs text-muted-foreground">
                        Expires: {new Date(alert.expires).toLocaleString()}
                      </p>
                    )}
                  </a>
                ))}
              </CardContent>
            )}
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Sources and limits</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <ul className="space-y-2">
                {result.sources.map((source) => (
                  <li key={source.url}>
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-2 text-sm text-primary underline-offset-4 hover:underline"
                    >
                      {source.title}
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                    {source.retrieved_at && (
                      <span className="ml-2 text-xs text-muted-foreground">
                        Retrieved {new Date(source.retrieved_at).toLocaleString()}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
              <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                {result.limitations.map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </section>
      )}
    </main>
  );
}
