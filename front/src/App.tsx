import { useEffect, useMemo, useState } from "react";

type Screen = "login" | "signup" | "chat" | "generating" | "board";
type Status = "backlog" | "todo" | "progress" | "review" | "done";
type Task = { id: string; title: string; priority: string; points: number; status: Status; owner: string };

const columns: { id: Status; label: string }[] = [
  { id: "backlog", label: "Backlog" },
  { id: "todo", label: "À faire" },
  { id: "progress", label: "En cours" },
  { id: "review", label: "Review" },
  { id: "done", label: "Terminé" },
];

const seedTasks: Task[] = [
  { id: "US-014", title: "Créer un système de connexion", priority: "Élevée", points: 5, status: "todo", owner: "ML" },
  { id: "US-018", title: "Parcourir les restaurants", priority: "Élevée", points: 5, status: "progress", owner: "AC" },
  { id: "US-021", title: "Configurer le paiement", priority: "Moyenne", points: 8, status: "backlog", owner: "JD" },
  { id: "US-006", title: "Créer le profil étudiant", priority: "Moyenne", points: 3, status: "review", owner: "ML" },
  { id: "US-002", title: "Initialiser l’application", priority: "Basse", points: 3, status: "done", owner: "AC" },
];

function Icon({ name, size = 18 }: { name: string; size?: number }) {
  const paths: Record<string, React.ReactNode> = {
    spark: <><path d="m12 3-1.2 4.2L7 9l3.8 1.8L12 15l1.2-4.2L17 9l-3.8-1.8L12 3Z"/><path d="m5 15-.7 2.3L2 18l2.3.7L5 21l.7-2.3L8 18l-2.3-.7L5 15Z"/></>,
    send: <><path d="m22 2-7 20-4-9-9-4 20-7Z"/><path d="M22 2 11 13"/></>,
    check: <path d="m5 12 4 4L19 6"/>,
    arrow: <path d="m9 18 6-6-6-6"/>,
    plus: <path d="M12 5v14M5 12h14"/>,
    google: <><path d="M21.4 12.2c0-.7-.1-1.4-.2-2H12v3.8h5.3a4.5 4.5 0 0 1-2 3v2.5h3.2c1.9-1.8 2.9-4.3 2.9-7.3Z"/><path d="M12 22c2.7 0 5-.9 6.6-2.4l-3.2-2.5c-.9.6-2 1-3.4 1-2.6 0-4.8-1.8-5.6-4.2H3.1v2.6A10 10 0 0 0 12 22Z"/><path d="M6.4 13.9a6 6 0 0 1 0-3.8V7.5H3.1a10 10 0 0 0 0 9l3.3-2.6Z"/><path d="M12 5.9c1.5 0 2.8.5 3.8 1.5l2.9-2.8A9.7 9.7 0 0 0 3.1 7.5l3.3 2.6C7.2 7.7 9.4 5.9 12 5.9Z"/></>,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}

function Brand() {
  return <div className="brand"><span className="logo"><Icon name="spark" size={18}/></span><span>Planora</span></div>;
}

function Auth({ signup, go }: { signup?: boolean; go: (screen: Screen) => void }) {
  return (
    <main className="auth-page">
      <header><Brand/><button className="text-button" onClick={() => go(signup ? "login" : "signup")}>{signup ? "Se connecter" : "Créer un compte"}</button></header>
      <section className="auth-card">
        <span className="auth-mark"><Icon name="spark" size={22}/></span>
        <h1>{signup ? "Créez votre espace projet" : "Bienvenue"}</h1>
        <p>{signup ? "Commencez à construire vos projets avec votre Scrum Master IA." : "Connectez-vous à votre espace projet."}</p>
        <form onSubmit={(e) => { e.preventDefault(); go("chat"); }}>
          {signup && <label>Nom<input placeholder="Votre nom" required/></label>}
          <label>Adresse e-mail<input type="email" placeholder="nom@entreprise.com" required/></label>
          <label>Mot de passe<input type="password" placeholder="8 caractères minimum" required/></label>
          {signup && <label>Confirmation du mot de passe<input type="password" placeholder="Confirmez votre mot de passe" required/></label>}
          {!signup && <div className="form-row"><label className="checkbox"><input type="checkbox"/>Se souvenir de moi</label><button type="button" className="link-button">Mot de passe oublié ?</button></div>}
          <button className="primary full" type="submit">{signup ? "Créer mon compte" : "Se connecter"}<Icon name="arrow" size={16}/></button>
        </form>
        <div className="divider"><span>ou</span></div>
        <button className="google-button"><Icon name="google" size={18}/>Continuer avec Google</button>
        <p className="auth-switch">{signup ? "Vous avez déjà un compte ?" : "Vous n’avez pas encore de compte ?"} <button onClick={() => go(signup ? "login" : "signup")}>{signup ? "Se connecter" : "Créer un compte"}</button></p>
      </section>
    </main>
  );
}

type ChatMessage = { role: "user" | "assistant"; content: string };
type Conversation = {
  conversation_id: string;
  status: "collecting" | "complete";
  progress: { answered: number; total: number };
  next_question: { id: string; title: string; text: string } | null;
  messages: ChatMessage[];
  summary?: {
    confirmed: Record<string, string>;
    unknown: string[];
    hypotheses: string[];
  };
};
type ApiError = { error: string };

const conversationStorageKey = "planora-po-conversation";
const answerFields = [
  { id: "features", label: "Fonctionnalités principales" },
  { id: "target_users", label: "Utilisateurs cibles" },
  { id: "technical_constraints", label: "Contraintes techniques" },
  { id: "developer_count", label: "Équipe disponible" },
  { id: "budget", label: "Budget" },
  { id: "deadline", label: "Date limite" },
];

function Progress({ board = false }: { board?: boolean }) {
  const steps = ["Projet", "Besoins", "Contraintes", "User Stories", "Backlog", "Scrum"];
  return <div className="progress-steps">{steps.map((step, index) => <div className={(board || index < 2) ? "complete" : index === 2 ? "active" : ""} key={step}><i>{(board || index < 2) ? <Icon name="check" size={10}/> : null}</i><span>{step}</span></div>)}</div>;
}

function ProjectChat() {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [restoring, setRestoring] = useState(true);
  const [editingAnswers, setEditingAnswers] = useState(false);
  const [editedAnswers, setEditedAnswers] = useState<Record<string, string>>({});
  const [savingAnswers, setSavingAnswers] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const conversationId = localStorage.getItem(conversationStorageKey);
    if (!conversationId) {
      setRestoring(false);
      return;
    }

    let cancelled = false;
    fetch(`/api/conversations/${encodeURIComponent(conversationId)}`)
      .then(async (response) => {
        const payload: Conversation | ApiError = await response.json();
        if (!response.ok || "error" in payload) {
          throw new Error("error" in payload ? payload.error : "Impossible de retrouver la conversation.");
        }
        if (!cancelled) setConversation(payload);
      })
      .catch((reason: unknown) => {
        if (!cancelled) setError(reason instanceof Error ? reason.message : "Impossible de retrouver la conversation.");
      })
      .finally(() => {
        if (!cancelled) setRestoring(false);
      });

    return () => { cancelled = true; };
  }, []);

  const submitMessage = async () => {
    const message = input.trim();
    if (!message || sending || restoring || conversation?.status === "complete") return;

    setSending(true);
    setError("");
    try {
      const endpoint = conversation
        ? `/api/conversations/${encodeURIComponent(conversation.conversation_id)}/messages`
        : "/api/conversations";
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const payload: Conversation | ApiError = await response.json();
      if (!response.ok || "error" in payload) {
        throw new Error("error" in payload ? payload.error : "Le message n’a pas pu être envoyé.");
      }
      localStorage.setItem(conversationStorageKey, payload.conversation_id);
      setConversation(payload);
      setInput("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Le service est momentanément indisponible.");
    } finally {
      setSending(false);
    }
  };

  const startEditingAnswers = () => {
    if (!conversation?.summary) return;
    const values: Record<string, string> = {
      description: conversation.summary.confirmed["Description initiale"] ?? "",
    };
    for (const field of answerFields) {
      values[field.id] = conversation.summary.confirmed[field.label] ?? "";
    }
    setEditedAnswers(values);
    setEditingAnswers(true);
    setError("");
  };

  const saveAnswers = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!conversation || savingAnswers) return;
    setSavingAnswers(true);
    setError("");
    try {
      const response = await fetch(
        `/api/conversations/${encodeURIComponent(conversation.conversation_id)}/answers`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            description: editedAnswers.description,
            answers: Object.fromEntries(answerFields.map((field) => [
              field.id,
              editedAnswers[field.id].trim() || null,
            ])),
          }),
        },
      );
      const payload: Conversation | ApiError = await response.json();
      if (!response.ok || "error" in payload) {
        throw new Error("error" in payload ? payload.error : "Les modifications n’ont pas pu être enregistrées.");
      }
      setConversation(payload);
      setEditingAnswers(false);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Impossible d’enregistrer les modifications.");
    } finally {
      setSavingAnswers(false);
    }
  };

  return (
    <main className="onboarding">
      <header className="app-header"><Brand/><Progress/><button className="avatar-button">AM</button></header>
      <section className="chat-stage">
        <div className="stage-title"><span className="ai-orb"><Icon name="spark" size={24}/></span><h1>Votre Product Owner IA</h1><p>Décrivez votre projet par écrit. Nous allons préciser vos besoins ensemble.</p></div>
        <div className="chat-thread">
          <div className="ai-line"><span><Icon name="spark" size={16}/></span><div><strong>Product Owner IA</strong><p>Bonjour. Décrivez votre idée avec vos propres mots. Je vous poserai ensuite quelques questions pour préciser les besoins du projet.</p></div></div>
          {conversation && <>
            {conversation.messages.map((message, index) => message.role === "user"
              ? <div className="user-bubble" key={`${message.role}-${index}`}>{message.content}</div>
              : <div className="ai-line conversation-message" key={`${message.role}-${index}`}><span><Icon name="spark" size={16}/></span><div><strong>Product Owner IA</strong><p>{message.content}</p></div></div>)}
          </>}
          {conversation?.next_question && <>
            <section className="question-card">
              <div className="question-heading"><div><span>Informations à compléter</span><h2>{conversation.progress.total - conversation.progress.answered} élément{conversation.progress.total - conversation.progress.answered > 1 ? "s" : ""} restant{conversation.progress.total - conversation.progress.answered > 1 ? "s" : ""}</h2></div><strong>{conversation.progress.answered}/{conversation.progress.total}</strong></div>
              <article className="open">
                <div className="question-index">{String(conversation.progress.answered + 1).padStart(2, "0")}</div>
                <div className="question-content"><h3>{conversation.next_question.title}</h3><p>{conversation.next_question.text}</p></div>
              </article>
            </section>
          </>}
          {conversation?.status === "complete" && conversation.summary && <section className="summary-card">
            <div className="summary-heading"><div><h2>Synthèse des besoins</h2><p>Les informations inconnues restent signalées, sans être inventées.</p></div>{!editingAnswers && <button className="answer-button" onClick={startEditingAnswers}>Modifier mes réponses</button>}</div>
            {editingAnswers
              ? <form className="summary-edit-form" onSubmit={(event) => void saveAnswers(event)}>
                <label>Description du projet<textarea required maxLength={10000} value={editedAnswers.description ?? ""} onChange={(event) => setEditedAnswers((values) => ({ ...values, description: event.target.value }))}/></label>
                {answerFields.map((field) => <label key={field.id}>{field.label}<textarea maxLength={10000} value={editedAnswers[field.id] ?? ""} placeholder="À préciser (laisser vide si inconnu)" onChange={(event) => setEditedAnswers((values) => ({ ...values, [field.id]: event.target.value }))}/></label>)}
                <div className="summary-edit-actions"><button type="button" className="answer-button" onClick={() => { setEditingAnswers(false); setError(""); }} disabled={savingAnswers}>Annuler</button><button type="submit" className="primary" disabled={savingAnswers}>{savingAnswers ? "Enregistrement…" : "Enregistrer les modifications"}</button></div>
              </form>
              : <>
                <h3>Informations confirmées</h3>
                <dl>{Object.entries(conversation.summary.confirmed).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
                {conversation.summary.unknown.length > 0 && <><h3>À préciser</h3><ul>{conversation.summary.unknown.map((item) => <li key={item}>{item}</li>)}</ul></>}
              </>}
          </section>}
        </div>
        {!conversation && <div className="idea-examples"><span>Essayez par exemple</span><button onClick={() => setInput("Je veux créer une application de livraison de repas pour les étudiants.")}>Application de livraison étudiante</button><button onClick={() => setInput("Je souhaite lancer une plateforme de réservation pour indépendants.")}>Plateforme de réservation</button></div>}
        {error && <p className="chat-error" role="alert">{error}</p>}
        <div className="main-composer"><textarea value={input} disabled={sending || conversation?.status === "complete"} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void submitMessage(); }}} placeholder={conversation?.next_question?.text ?? "Décrivez votre projet..."} aria-label="Votre message au Product Owner"/><button onClick={() => void submitMessage()} disabled={sending || restoring || conversation?.status === "complete"} aria-label="Envoyer le message"><Icon name="send" size={18}/></button></div>
        <p className="composer-note">{restoring ? "Restauration de votre conversation…" : sending ? "Envoi de votre réponse…" : "Votre conversation est enregistrée et pourra être reprise plus tard."}</p>
      </section>
    </main>
  );
}

function Generating({ go }: { go: (screen: Screen) => void }) {
  return <main className="generation"><Brand/><section><span className="generating-orb"><Icon name="spark" size={27}/></span><p className="kicker">Construction de votre projet</p><h1>Votre Scrum Master prépare le plan.</h1><p>Nous transformons vos réponses en une organisation claire et réaliste.</p><div className="generation-list">{["Analyse du projet", "Génération des User Stories", "Construction du backlog", "Priorisation Scrum", "Préparation du tableau"].map((item, i) => <div className={i < 4 ? "done" : "loading"} key={item}>{i < 4 ? <Icon name="check" size={14}/> : <span/>}<strong>{item}</strong><em>{i < 4 ? "Terminé" : "En cours"}</em></div>)}</div><button className="primary" onClick={() => go("board")}>Afficher mon espace projet<Icon name="arrow" size={16}/></button></section></main>;
}

function Board() {
  const [tasks, setTasks] = useState(seedTasks);
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("J’ai organisé le Sprint 1 autour de l’inscription et de la découverte des restaurants.");
  const points = useMemo(() => tasks.reduce((sum, task) => sum + task.points, 0), [tasks]);
  const move = (id: string, status: Status) => setTasks((all) => all.map((task) => task.id === id ? { ...task, status } : task));
  const send = () => {
    if (!message.trim()) return;
    if (message.toLowerCase().includes("paiement") || message.includes("US-021")) { move("US-021", "backlog"); setReply("C’est fait. J’ai déplacé US-021 — Configurer le paiement dans le Sprint 2."); }
    else setReply("Cette tâche est prioritaire car elle débloque le parcours principal et trois autres tâches du Sprint 1.");
    setMessage("");
  };
  return <main className="board-app">
    <header className="app-header"><Brand/><div className="project-name"><span>Projet</span><strong>Campus Eats</strong></div><button className="avatar-button">AM</button></header>
    <div className="final-layout">
      <section className="kanban-panel">
        <div className="kanban-title"><div><span className="blue-kicker">Sprint 1 · Actif</span><h1>Expérience de commande initiale</h1><p>Permettre aux étudiants de découvrir un restaurant et de créer leur compte.</p></div><button className="primary"><Icon name="plus" size={16}/>Nouvelle tâche</button></div>
        <div className="sprint-bar"><div><strong>3 / {points} points</strong><span>Progression du sprint</span></div><div className="bar"><i/></div><span>28 juin</span></div>
        <div className="kanban-grid">{columns.map((column) => { const items = tasks.filter((task) => task.status === column.id); return <section className="kanban-column" key={column.id} onDragOver={(e) => e.preventDefault()} onDrop={(e) => move(e.dataTransfer.getData("task"), column.id)}><header><div><i className={column.id}/><strong>{column.label}</strong><span>{items.length}</span></div><button><Icon name="plus" size={14}/></button></header><div className="cards">{items.map((task) => <article className="task" draggable onDragStart={(e) => e.dataTransfer.setData("task", task.id)} key={task.id}><span>{task.id}</span><h3>{task.title}</h3><div><em className={task.priority === "Élevée" ? "high" : ""}>{task.priority}</em><small>{task.points} points</small><i>{task.owner}</i></div></article>)}{items.length === 0 && <div className="empty-drop">Déposer ici</div>}</div></section>})}</div>
      </section>
      <aside className="board-chat">
        <header><span className="ai-orb small"><Icon name="spark" size={18}/></span><div><h2>Scrum Master IA</h2><p>Connecté au tableau</p></div><i/></header>
        <div className="chat-context"><span>Contexte actuel</span><strong>Sprint 1 · 5 tâches · 24 points</strong></div>
        <div className="board-thread"><div className="ai-line compact"><span><Icon name="spark" size={14}/></span><div><strong>Scrum Master IA</strong><p>{reply}</p></div></div><div className="user-bubble small">Pourquoi cette tâche est-elle prioritaire ?</div></div>
        <div className="board-composer"><div className="suggestions"><button onClick={() => setMessage("Pourquoi cette tâche est prioritaire ?")}>Expliquer une priorité</button><button onClick={() => setMessage("Déplace le paiement au Sprint 2")}>Réorganiser le sprint</button></div><div><textarea value={message} onChange={(e) => setMessage(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); send(); }}} placeholder="Demandez une modification..."/><button onClick={send}><Icon name="send" size={17}/></button></div><p><Icon name="spark" size={12}/>L’IA peut modifier directement le tableau</p></div>
      </aside>
    </div>
  </main>;
}

export default function App() {
  const [screen, setScreen] = useState<Screen>("login");
  if (screen === "login") return <Auth go={setScreen}/>;
  if (screen === "signup") return <Auth signup go={setScreen}/>;
  if (screen === "chat") return <ProjectChat/>;
  if (screen === "generating") return <Generating go={setScreen}/>;
  return <Board/>;
}
