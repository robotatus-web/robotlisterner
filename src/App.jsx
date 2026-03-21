import { useState } from "react";
import {
  AlertCircle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  FileText,
  Image as ImageIcon,
  Loader2,
  Trash2,
  UploadCloud,
} from "lucide-react";

const AGENTS = [
  {
    key: "accountant",
    name: "Könyvelő - Számolás",
    systemPrompt:
      "Te egy precíz könyvelő vagy, aki számításokat végez. Részletesen számolj, mutasd be a számítási lépéseket és adj pontos eredményeket.",
    task: "Végezd el a könyvelési számításokat a csatolt fájlok alapján. Számold ki az összes tranzakciót, egyenleget, bevételt és kiadást.",
  },
  {
    key: "analyst",
    name: "Pénzügyi Elemző - Kiértékelés",
    systemPrompt:
      "Te egy tapasztalt pénzügyi elemző vagy. Kritikusan értékeld a számokat, keress mintázatokat és adj stratégiai tanácsokat.",
    task: "Értékeld ki az előző ágens számításait. Adj betekintést, azonosítsd a trendeket, anomáliákat és adj javaslatokat.",
  },
];

const formatFileSize = (bytes) => {
  if (!bytes && bytes !== 0) return "-";
  const units = ["B", "KB", "MB", "GB"];
  let index = 0;
  let size = bytes;
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024;
    index += 1;
  }
  return `${size.toFixed(size < 10 && index > 0 ? 1 : 0)} ${units[index]}`;
};

const mapFileToContent = (fileItem) => {
  if (fileItem.readError) return null;
  if (fileItem.kind === "document") {
    return {
      type: "document",
      source: {
        type: "base64",
        media_type: "application/pdf",
        data: fileItem.content,
      },
    };
  }
  if (fileItem.kind === "image") {
    return {
      type: "image",
      source: {
        type: "base64",
        media_type: fileItem.mediaType,
        data: fileItem.content,
      },
    };
  }
  return {
    type: "text",
    text: fileItem.content,
  };
};

const readFileAsBase64 = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result;
      if (typeof result !== "string") {
        reject(new Error("Nem sikerült beolvasni a fájlt."));
        return;
      }
      const base64 = result.split(",")[1] || "";
      resolve(base64);
    };
    reader.onerror = () => reject(new Error("Nem sikerült beolvasni a fájlt."));
    reader.readAsDataURL(file);
  });

const readFileAsText = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result;
      if (typeof result !== "string") {
        reject(new Error("Nem sikerült beolvasni a fájlt."));
        return;
      }
      resolve(result);
    };
    reader.onerror = () => reject(new Error("Nem sikerült beolvasni a fájlt."));
    reader.readAsText(file);
  });

const isSupportedFile = (file) => {
  const supportedTypes = [
    "application/pdf",
    "text/csv",
    "text/xml",
    "application/xml",
    "image/png",
    "image/jpeg",
  ];
  return supportedTypes.includes(file.type);
};

const getFileKind = (file) => {
  if (file.type === "application/pdf") return "document";
  if (file.type.startsWith("image/")) return "image";
  return "text";
};

export default function App() {
  const [apiKey, setApiKey] = useState("");
  const [showSettings, setShowSettings] = useState(true);
  const [generalInstructions, setGeneralInstructions] = useState("");
  const [extraPrompts, setExtraPrompts] = useState({
    accountant: "",
    analyst: "",
  });
  const [files, setFiles] = useState([]);
  const [results, setResults] = useState({
    accountant: { status: "idle", output: "" },
    analyst: { status: "idle", output: "" },
  });
  const [loadingStep, setLoadingStep] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  const handleExtraPromptChange = (key, value) => {
    setExtraPrompts((prev) => ({ ...prev, [key]: value }));
  };

  const handleFiles = async (selectedFiles) => {
    const incoming = Array.from(selectedFiles || []);
    if (incoming.length === 0) return;

    const prepared = await Promise.all(
      incoming.map(async (file) => {
        if (!isSupportedFile(file)) {
          return {
            id: `${file.name}-${file.size}-${file.lastModified}`,
            name: file.name,
            size: file.size,
            type: file.type || "unknown",
            kind: "text",
            content: "",
            readError: `Nem támogatott fájltípus: ${file.type || "ismeretlen"}`,
          };
        }

        const kind = getFileKind(file);
        try {
          const content =
            kind === "text" ? await readFileAsText(file) : await readFileAsBase64(file);
          return {
            id: `${file.name}-${file.size}-${file.lastModified}`,
            name: file.name,
            size: file.size,
            type: file.type,
            kind,
            content,
            mediaType: file.type,
            readError: "",
          };
        } catch (error) {
          return {
            id: `${file.name}-${file.size}-${file.lastModified}`,
            name: file.name,
            size: file.size,
            type: file.type,
            kind,
            content: "",
            mediaType: file.type,
            readError: error?.message || "Nem sikerült beolvasni a fájlt.",
          };
        }
      })
    );

    setFiles((prev) => [...prev, ...prepared]);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    handleFiles(event.dataTransfer.files);
  };

  const removeFile = (id) => {
    setFiles((prev) => prev.filter((file) => file.id !== id));
  };

  const buildInstructionText = ({ task, extraPrompt }) => {
    const parts = [];
    if (generalInstructions.trim()) {
      parts.push(`Általános instrukciók:\n${generalInstructions.trim()}`);
    }
    if (task) {
      parts.push(`Feladat:\n${task}`);
    }
    if (extraPrompt.trim()) {
      parts.push(`Extra prompt:\n${extraPrompt.trim()}`);
    }
    return parts.join("\n\n");
  };

  const callAnthropic = async ({ systemPrompt, content }) => {
    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: "claude-sonnet-4-20250514",
        max_tokens: 4000,
        system: systemPrompt,
        messages: [
          {
            role: "user",
            content,
          },
        ],
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API hiba (${response.status}): ${errorText}`);
    }

    const data = await response.json();
    const textParts = (data.content || [])
      .filter((item) => item.type === "text")
      .map((item) => item.text);
    return textParts.join("\n\n");
  };

  const runPipeline = async () => {
    setErrorMessage("");
    setResults({
      accountant: { status: "idle", output: "" },
      analyst: { status: "idle", output: "" },
    });

    if (!apiKey.trim()) {
      setErrorMessage("Hiányzik az Anthropic API kulcs.");
      return;
    }

    if (files.length === 0 && !generalInstructions.trim()) {
      setErrorMessage("Adj meg legalább egy fájlt vagy általános instrukciót.");
      return;
    }

    const hasReadErrors = files.some((file) => file.readError);
    if (hasReadErrors) {
      setErrorMessage("Egy vagy több fájl beolvasása sikertelen. Kérlek ellenőrizd a listát.");
      return;
    }

    try {
      setLoadingStep(1);
      const fileContents = files.map(mapFileToContent).filter(Boolean);
      const firstAgent = AGENTS[0];
      const firstInstructionText = buildInstructionText({
        task: firstAgent.task,
        extraPrompt: extraPrompts[firstAgent.key] || "",
      });
      const firstContent = [...fileContents];
      if (firstInstructionText.trim()) {
        firstContent.push({ type: "text", text: firstInstructionText });
      }

      const firstOutput = await callAnthropic({
        systemPrompt: firstAgent.systemPrompt,
        content: firstContent,
      });

      setResults((prev) => ({
        ...prev,
        accountant: { status: "success", output: firstOutput },
      }));

      setLoadingStep(2);
      const secondAgent = AGENTS[1];
      const secondInstructionText = buildInstructionText({
        task: secondAgent.task,
        extraPrompt: extraPrompts[secondAgent.key] || "",
      });
      const secondContent = [
        {
          type: "text",
          text: `Előző ágens válasza:\n${firstOutput}\n\n${secondInstructionText}`,
        },
      ];

      const secondOutput = await callAnthropic({
        systemPrompt: secondAgent.systemPrompt,
        content: secondContent,
      });

      setResults((prev) => ({
        ...prev,
        analyst: { status: "success", output: secondOutput },
      }));
    } catch (error) {
      const message = error?.message || "Ismeretlen hiba történt.";
      if (loadingStep === 1) {
        setResults((prev) => ({
          ...prev,
          accountant: { status: "error", output: message },
        }));
      } else {
        setResults((prev) => ({
          ...prev,
          analyst: { status: "error", output: message },
        }));
      }
    } finally {
      setLoadingStep(null);
    }
  };

  const isRunning = loadingStep !== null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-slate-100 text-slate-800">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-8 px-6 py-10">
        <header className="space-y-3">
          <span className="inline-flex w-fit items-center gap-2 rounded-full bg-emerald-100 px-4 py-1 text-sm font-semibold text-emerald-700">
            Claude multi-agent pipeline
          </span>
          <h1 className="text-3xl font-semibold text-slate-900">
            Könyvelő + Pénzügyi elemző pipeline
          </h1>
          <p className="max-w-2xl text-sm text-slate-600">
            Tölts fel dokumentumokat, add meg az instrukciókat, majd futtasd a kétlépéses
            elemzést az Anthropic Claude API-n keresztül.
          </p>
        </header>

        <section className="rounded-3xl bg-white/70 p-6 shadow-xl shadow-emerald-100/50 backdrop-blur">
          <button
            type="button"
            className="flex w-full items-center justify-between text-left text-lg font-semibold text-slate-900"
            onClick={() => setShowSettings((prev) => !prev)}
          >
            API konfiguráció
            {showSettings ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
          </button>
          {showSettings && (
            <div className="mt-4 grid gap-4 sm:grid-cols-[1fr_auto] sm:items-center">
              <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
                Anthropic API kulcs
                <input
                  type="password"
                  value={apiKey}
                  onChange={(event) => setApiKey(event.target.value)}
                  placeholder="sk-ant-..."
                  className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm shadow-sm focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100"
                />
              </label>
              <div className="rounded-2xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-xs text-emerald-700">
                Az API kulcsot csak a böngésző tárolja, a kód nem menti szerverre.
              </div>
            </div>
          )}
        </section>

        <section className="rounded-3xl bg-white/80 p-6 shadow-lg shadow-emerald-100/40 backdrop-blur">
          <h2 className="text-lg font-semibold text-slate-900">Fájlfeltöltés</h2>
          <div
            className="mt-4 flex flex-col items-center gap-3 rounded-2xl border-2 border-dashed border-emerald-200 bg-emerald-50/50 px-6 py-8 text-center"
            onDragOver={(event) => event.preventDefault()}
            onDrop={handleDrop}
          >
            <UploadCloud className="h-8 w-8 text-emerald-500" />
            <p className="text-sm text-slate-600">
              Húzd ide a fájlokat vagy kattints a feltöltéshez (PDF, CSV, XML, PNG, JPG).
            </p>
            <label className="cursor-pointer rounded-full bg-emerald-500 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-emerald-600">
              Fájlok kiválasztása
              <input
                type="file"
                multiple
                accept=".pdf,.csv,.xml,image/png,image/jpeg"
                className="hidden"
                onChange={(event) => handleFiles(event.target.files)}
              />
            </label>
          </div>

          {files.length > 0 && (
            <div className="mt-6 space-y-3">
              {files.map((file) => (
                <div
                  key={file.id}
                  className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm"
                >
                  <div className="flex items-center gap-3">
                    {file.kind === "image" ? (
                      <ImageIcon className="h-5 w-5 text-emerald-500" />
                    ) : (
                      <FileText className="h-5 w-5 text-emerald-500" />
                    )}
                    <div>
                      <p className="font-medium text-slate-800">{file.name}</p>
                      <p className="text-xs text-slate-500">
                        {file.type || "ismeretlen"} • {formatFileSize(file.size)}
                      </p>
                      {file.readError && (
                        <p className="text-xs text-rose-500">{file.readError}</p>
                      )}
                    </div>
                  </div>
                  <button
                    type="button"
                    className="inline-flex items-center gap-2 rounded-full border border-rose-200 px-3 py-1 text-xs font-semibold text-rose-500 hover:bg-rose-50"
                    onClick={() => removeFile(file.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                    Törlés
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="rounded-3xl bg-white/80 p-6 shadow-lg shadow-emerald-100/40 backdrop-blur">
          <h2 className="text-lg font-semibold text-slate-900">Instrukciók</h2>
          <div className="mt-4 grid gap-6">
            <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
              Általános instrukciók (opcionális)
              <textarea
                value={generalInstructions}
                onChange={(event) => setGeneralInstructions(event.target.value)}
                placeholder="Pl. magyar nyelv, táblázatos összegzés..."
                className="min-h-[110px] rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-sm focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100"
              />
            </label>

            {AGENTS.map((agent) => (
              <div key={agent.key} className="rounded-2xl border border-emerald-100 bg-emerald-50/40 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-emerald-700">{agent.name}</p>
                    <p className="text-xs text-emerald-600">{agent.task}</p>
                  </div>
                </div>
                <label className="mt-3 flex flex-col gap-2 text-xs font-medium text-emerald-700">
                  Extra prompt (opcionális)
                  <textarea
                    value={extraPrompts[agent.key]}
                    onChange={(event) => handleExtraPromptChange(agent.key, event.target.value)}
                    placeholder="Adj meg egyedi instrukciókat ehhez az ágenshez..."
                    className="min-h-[90px] rounded-xl border border-emerald-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100"
                  />
                </label>
              </div>
            ))}
          </div>
        </section>

        {errorMessage && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600">
            {errorMessage}
          </div>
        )}

        <section className="flex flex-col gap-4 rounded-3xl bg-white/90 p-6 shadow-xl shadow-emerald-100/40 backdrop-blur">
          <button
            type="button"
            onClick={runPipeline}
            disabled={isRunning}
            className="inline-flex items-center justify-center gap-3 rounded-full bg-emerald-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-200/60 transition hover:bg-emerald-600 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isRunning ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Futás... ({loadingStep}/2)
              </>
            ) : (
              "Pipeline futtatása"
            )}
          </button>
        </section>

        <section className="grid gap-6 md:grid-cols-2">
          {AGENTS.map((agent) => {
            const result = results[agent.key];
            const isSuccess = result.status === "success";
            const isError = result.status === "error";
            return (
              <div
                key={agent.key}
                className={`rounded-3xl border-2 bg-white/80 p-5 shadow-lg shadow-emerald-100/40 backdrop-blur ${
                  isSuccess
                    ? "border-emerald-300"
                    : isError
                    ? "border-rose-300"
                    : "border-transparent"
                }`}
              >
                <div className="flex items-center gap-2">
                  {isSuccess ? (
                    <CheckCircle className="h-5 w-5 text-emerald-500" />
                  ) : isError ? (
                    <AlertCircle className="h-5 w-5 text-rose-500" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-slate-300" />
                  )}
                  <h3 className="text-sm font-semibold text-slate-800">{agent.name}</h3>
                </div>
                <p className="mt-3 whitespace-pre-wrap text-sm text-slate-700">
                  {result.output ||
                    "Még nincs válasz. Indítsd el a pipeline-t a feldolgozáshoz."}
                </p>
              </div>
            );
          })}
        </section>
      </div>
    </div>
  );
}
