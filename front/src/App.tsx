import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import {
  ApiError,
  answerClarification,
  createProject,
  generateProject,
  login,
  register,
  setAuthToken,
  startClarification,
  updateTask,
  type BacklogTask,
  type ClarifyingQuestion,
  type ProjectDetail,
  type TaskStatus,
} from "./api";

type Screen = "login" | "signup" | "chat" | "generating" | "board";

const columns: { id: TaskStatus; label: string }[] = [
  { id: "backlog", label: "Backlog" },
  { id: "todo", label: "À faire" },
  { id: "in_progress", label: "En cours" },
  { id: "review", label: "Review" },
  { id: "done", label: "Terminé" },
];

function errorMessage(error: unknown): string {
  return error instanceof ApiError || error instanceof Error ? error.message : "Une erreur inattendue est survenue.";
}

function priorityLabel(priority: BacklogTask["priority"]): string {
  return { critical: "Critique", high: "Élevée", medium: "Moyenne", low: "Basse" }[priority];
}

function Icon({ name, size = 18 }: { name: string; size?: number }) {
  const paths: Record<string, ReactNode> = {
    spark: <><path d="m12 3-1.2 4.2L7 9l3.8 1.8L12 15l1.2-4.2L17 9l-3.8-1.8L12 3Z"/><path d="m5 15-.7 2.3L2 18l2.3.7L5 21l.7-2.3L8 18l-2.3-.7L5 15Z"/></>,
    send: <><path d="m22 2-7 20-4-9-9-4 20-7Z"/><path d="M22 2 11 13"/></>,
    check: <path d="m5 12 4 4L19 6"/>,
    arrow: <path d="m9 18 6-6-6-6"/>,
    plus: <path d="M12 5v14M5 12h14"/>,
    retry: <><path d="M20 11a8.1 8.1 0 0 0-15.5-2M4 5v4h4"/><path d="M4 13a8.1 8.1 0 0 0 15.5 2M20 19v-4h-4"/></>,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}

function Brand() {
  return <div className="brand"><span className="logo"><Icon name="spark" size={18}/></span><span>Planora</span></div>;
}

function Auth({ signup, go, onAuthenticated }: { signup?: boolean; go: (screen: Screen) => void; onAuthenticated: () => void }) {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  return (
    <main className="auth-page">
      <header><Brand/><button className="text-button" onClick={() => go(signup ? "login" : "signup")}>{signup ? "Se connecter" : "Créer un compte"}</button></header>
      <section className="auth-card">
        <span className="auth-mark"><Icon name="spark" size={22}/></span>
        <h1>{signup ? "Créez votre espace projet" : "Bienvenue"}</h1>
        <p>{signup ? "Commencez à construire vos projets avec votre Scrum Master IA." : "Connectez-vous à votre espace projet."}</p>
        <form onSubmit={(event) => {
          event.preventDefault();
          const form = new FormData(event.currentTarget);
          const name = String(form.get("name") || "");
          const email = String(form.get("email") || "");
          const password = String(form.get("password") || "");
          const confirmation = String(form.get("confirmation") || "");
          if (signup && password !== confirmation) { setError("Les mots de passe ne correspondent pas."); return; }
          setBusy(true);
          setError(null);
          void (signup ? register(name, email, password) : login(email, password))
            .then((response) => { setAuthToken(response.token); onAuthenticated(); go("chat"); })
            .catch((requestError: unknown) => setError(errorMessage(requestError)))
            .finally(() => setBusy(false));
        }}>
          {signup && <label>Nom<input name="name" placeholder="Votre nom" required/></label>}
          <label>Adresse e-mail<input name="email" type="email" placeholder="nom@entreprise.com" required/></label>
          <label>Mot de passe<input name="password" type="password" placeholder="8 caractères minimum" minLength={8} required/></label>
          {signup && <label>Confirmation du mot de passe<input name="confirmation" type="password" placeholder="Confirmez votre mot de passe" minLength={8} required/></label>}
          {error && <p className="error-alert" role="alert">{error}</p>}
          <button className="primary full" type="submit" disabled={busy}>{busy ? "Connexion..." : signup ? "Créer mon compte" : "Se connecter"}<Icon name="arrow" size={16}/></button>
        </form>
      </section>
    </main>
  );
}

function Progress({ board = false }: { board?: boolean }) {
  const steps = ["Projet", "Besoins", "Contraintes", "User Stories", "Backlog", "Scrum"];
  return <div className="progress-steps">{steps.map((step, index) => <div className={(board || index < 2) ? "complete" : index === 2 ? "active" : ""} key={step}><i>{(board || index < 2) ? <Icon name="check" size={10}/> : null}</i><span>{step}</span></div>)}</div>;
}

function ProjectChat({ go, onProjectCreated }: { go: (screen: Screen) => void; onProjectCreated: (id: string) => void }) {
  const [description, setDescription] = useState("");
  const [projectId, setProjectId] = useState<string | null>(null);
  const [question, setQuestion] = useState<ClarifyingQuestion | null>(null);
  const [agentMessage, setAgentMessage] = useState("Bonjour. Décrivez votre projet avec vos propres mots. Je vais ensuite vous poser quelques questions pour comprendre vos besoins.");
  const [textAnswer, setTextAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startProject = async () => {
    if (!description.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const name = description.trim().split(/[.!?]/)[0].slice(0, 80) || "Nouveau projet";
      const project = projectId
        ? { id: projectId }
        : await createProject(name, description.trim());
      setProjectId(project.id);
      onProjectCreated(project.id);
      const clarification = await startClarification(project.id);
      setQuestion(clarification.question);
      setAgentMessage(clarification.message);
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusy(false);
    }
  };

  const submitAnswer = async (answer: string) => {
    if (!projectId || !question || !answer.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const clarification = await answerClarification(projectId, question.id, answer.trim());
      setQuestion(clarification.question);
      setAgentMessage(clarification.message);
      setTextAnswer("");
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusy(false);
    }
  };

  const started = projectId !== null;
  return (
    <main className="onboarding">
      <header className="app-header"><Brand/><Progress/><button className="avatar-button">AM</button></header>
      <section className="chat-stage">
        <div className="stage-title"><span className="ai-orb"><Icon name="spark" size={24}/></span><h1>Votre Scrum Master IA</h1><p>Décrivez votre projet. Je vais vous aider à le transformer en un plan Scrum structuré.</p></div>
        <div className="chat-thread">
          <div className="ai-line"><span><Icon name="spark" size={16}/></span><div><strong>Product Owner IA</strong><p>{agentMessage}</p></div></div>
          {started && <>
            <div className="user-bubble">{description}</div>
            {question ? <section className="question-card">
              <div className="question-heading"><div><span>Information à compléter</span><h2>{question.field_key.replace(/_/g, " ")}</h2></div><strong>IA</strong></div>
              <article className="open">
                <div className="question-index">?</div>
                <div className="question-content"><h3>{question.question}</h3><p>{question.why_it_matters}</p>
                  {question.question_type === "single_choice" ? <div className="quick-choices">{question.choices.map((choice) => <button disabled={busy} key={choice} onClick={() => void submitAnswer(choice)}>{choice}</button>)}</div> : <div className="text-answer"><input value={textAnswer} disabled={busy} onChange={(event) => setTextAnswer(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") void submitAnswer(textAnswer); }} placeholder="Votre réponse..."/><button className="answer-button" disabled={busy} onClick={() => void submitAnswer(textAnswer)}>Envoyer</button></div>}
                </div>
              </article>
            </section> : <div className="ready-card"><Icon name="check"/><div><strong>Le projet est suffisamment défini</strong><p>Je peux maintenant générer les User Stories, le backlog et les premiers sprints.</p></div><button className="primary" disabled={busy} onClick={() => go("generating")}>Générer mon backlog<Icon name="arrow" size={16}/></button></div>}
          </>}
        </div>
        {error && <p className="error-alert" role="alert">{error}</p>}
        {!started && <><div className="idea-examples"><span>Essayez par exemple</span><button onClick={() => setDescription("Je veux créer une application de livraison de repas pour les étudiants.")}>Application de livraison étudiante</button><button onClick={() => setDescription("Je souhaite lancer une plateforme de réservation pour indépendants.")}>Plateforme de réservation</button></div><div className="main-composer"><textarea value={description} disabled={busy} onChange={(event) => setDescription(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void startProject(); }}} placeholder="Décrivez votre projet..."/><button disabled={busy} onClick={() => void startProject()}><Icon name="send" size={18}/></button></div></>}
        {started && error && <button className="primary retry-project" disabled={busy} onClick={() => void startProject()}>Réessayer la clarification<Icon name="retry" size={16}/></button>}
        <p className="composer-note">Les données sont sauvegardées par le backend.</p>
      </section>
    </main>
  );
}

function Generating({ projectId, onGenerated, go }: { projectId: string | null; onGenerated: (project: ProjectDetail) => void; go: (screen: Screen) => void }) {
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const completedProject = useRef<string | null>(null);

  useEffect(() => {
    if (!projectId || completedProject.current === `${projectId}:${attempt}`) return;
    setElapsedSeconds(0);
    let active = true;
    const startedAt = Date.now();
    const timer = window.setInterval(() => {
      if (active) setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000));
    }, 1000);
    const request = window.setTimeout(() => {
      if (!active) return;
      completedProject.current = `${projectId}:${attempt}`;
      void generateProject(projectId).then((result) => {
        if (!active) return;
        onGenerated(result.project);
        go("board");
      }).catch((requestError: unknown) => {
        if (active) setError(errorMessage(requestError));
      });
    }, 0);
    return () => {
      active = false;
      window.clearTimeout(request);
      window.clearInterval(timer);
    };
  }, [attempt, go, onGenerated, projectId]);

  return <main className="generation"><Brand/><section><span className="generating-orb"><Icon name="spark" size={27}/></span><p className="kicker">Construction de votre projet</p><h1>Votre Scrum Master prépare le plan.</h1><p>{error ? "La génération doit être relancée." : `Les agents Gemini travaillent sur votre backlog. ${elapsedSeconds}s écoulées.`}</p><div className="generation-list">{["Analyse du projet", "Génération des User Stories", "Construction du backlog", "Priorisation Scrum", "Préparation du tableau"].map((item, index) => <div className={error ? "" : "loading"} key={item}>{error ? <Icon name="retry" size={14}/> : index === 0 ? <span/> : <span/>}<strong>{item}</strong><em>{error ? "En attente" : "En cours"}</em></div>)}</div>{error && <><p className="error-alert" role="alert">{error}</p><button className="primary" onClick={() => { setError(null); setAttempt((value) => value + 1); }}>Réessayer<Icon name="retry" size={16}/></button></>}</section></main>;
}

function Board({ project }: { project: ProjectDetail }) {
  const [tasks, setTasks] = useState(project.tasks);
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("Votre backlog est synchronisé avec le backend. Déplacez une carte pour enregistrer son statut.");
  const [error, setError] = useState<string | null>(null);
  useEffect(() => setTasks(project.tasks), [project]);
  const points = useMemo(() => tasks.reduce((sum, task) => sum + (task.estimate_points ?? 0), 0), [tasks]);
  const activeSprint = project.sprints.at(0);

  const move = async (id: string, status: TaskStatus) => {
    const previous = tasks;
    setTasks((all) => all.map((task) => task.id === id ? { ...task, status } : task));
    setError(null);
    try {
      const result = await updateTask(project.id, id, { status });
      setTasks((all) => all.map((task) => task.id === id ? result.task : task));
    } catch (requestError) {
      setTasks(previous);
      setError(errorMessage(requestError));
    }
  };

  const send = () => {
    if (!message.trim()) return;
    setReply("Les changements du tableau sont enregistrés automatiquement. Pour modifier les besoins, créez une nouvelle clarification via l’API.");
    setMessage("");
  };

  return <main className="board-app">
    <header className="app-header"><Brand/><div className="project-name"><span>Projet</span><strong>{project.name}</strong></div><button className="avatar-button">AM</button></header>
    <div className="final-layout">
      <section className="kanban-panel">
        <div className="kanban-title"><div><span className="blue-kicker">{activeSprint ? `Sprint ${activeSprint.number}` : "Backlog généré"}</span><h1>{activeSprint?.goal || "Plan de projet"}</h1><p>{project.context?.product_summary || project.description}</p></div><button className="primary" title="Les nouvelles tâches sont générées via le backlog IA"><Icon name="plus" size={16}/>Nouvelle tâche</button></div>
        <div className="sprint-bar"><div><strong>{points} points</strong><span>Charge estimée totale</span></div><div className="bar"><i/></div><span>{tasks.length} tâches</span></div>
        <div className="kanban-grid">{columns.map((column) => { const items = tasks.filter((task) => task.status === column.id); const className = column.id === "in_progress" ? "progress" : column.id; return <section className="kanban-column" key={column.id} onDragOver={(event) => event.preventDefault()} onDrop={(event) => void move(event.dataTransfer.getData("task"), column.id)}><header><div><i className={className}/><strong>{column.label}</strong><span>{items.length}</span></div><button aria-label={`Ajouter dans ${column.label}`}><Icon name="plus" size={14}/></button></header><div className="cards">{items.map((task) => <article className="task" draggable onDragStart={(event) => event.dataTransfer.setData("task", task.id)} key={task.id} title={task.priority_reason}><span>{task.id.slice(0, 8).toUpperCase()}</span><h3>{task.title}</h3><div><em className={task.priority === "critical" || task.priority === "high" ? "high" : ""}>{priorityLabel(task.priority)}</em><small>{task.estimate_points ?? "?"} points</small><i>IA</i></div></article>)}{items.length === 0 && <div className="empty-drop">Déposer ici</div>}</div></section>; })}</div>
      </section>
      <aside className="board-chat">
        <header><span className="ai-orb small"><Icon name="spark" size={18}/></span><div><h2>Scrum Master IA</h2><p>Tableau synchronisé</p></div><i/></header>
        <div className="chat-context"><span>Contexte actuel</span><strong>{project.user_stories.length} stories · {tasks.length} tâches</strong></div>
        <div className="board-thread"><div className="ai-line compact"><span><Icon name="spark" size={14}/></span><div><strong>Scrum Master IA</strong><p>{reply}</p></div></div>{error && <p className="error-alert" role="alert">{error}</p>}</div>
        <div className="board-composer"><div className="suggestions"><button onClick={() => setMessage("Pourquoi cette tâche est-elle prioritaire ?")}>Expliquer une priorité</button><button onClick={() => setMessage("Comment modifier le sprint ?")}>Planifier le sprint</button></div><div><textarea value={message} onChange={(event) => setMessage(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); send(); }}} placeholder="Demandez une explication..."/><button onClick={send}><Icon name="send" size={17}/></button></div><p><Icon name="spark" size={12}/>Le déplacement d’une carte est enregistré.</p></div>
      </aside>
    </div>
  </main>;
}

export default function App() {
  const [authenticated, setAuthenticated] = useState(() => Boolean(localStorage.getItem("planora_token")));
  const [screen, setScreen] = useState<Screen>(() => localStorage.getItem("planora_token") ? "chat" : "login");
  const [projectId, setProjectId] = useState<string | null>(null);
  const [project, setProject] = useState<ProjectDetail | null>(null);
  if ((!authenticated && screen !== "signup") || screen === "login") return <Auth go={setScreen} onAuthenticated={() => setAuthenticated(true)}/>;
  if (screen === "signup") return <Auth signup go={setScreen} onAuthenticated={() => setAuthenticated(true)}/>;
  if (screen === "chat") return <ProjectChat go={setScreen} onProjectCreated={setProjectId}/>;
  if (screen === "generating") return <Generating projectId={projectId} go={setScreen} onGenerated={setProject}/>;
  return project ? <Board project={project}/> : <ProjectChat go={setScreen} onProjectCreated={setProjectId}/>;
}
