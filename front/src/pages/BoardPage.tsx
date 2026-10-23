import { useMemo, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

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

function Icon({ name, size = 18 }: { name: string; size?: number }) {
  const paths: Record<string, React.ReactNode> = {
    spark: <><path d="m12 3-1.2 4.2L7 9l3.8 1.8L12 15l1.2-4.2L17 9l-3.8-1.8L12 3Z"/><path d="m5 15-.7 2.3L2 18l2.3.7L5 21l.7-2.3L8 18l-2.3-.7L5 15Z"/></>,
    send: <><path d="m22 2-7 20-4-9-9-4 20-7Z"/><path d="M22 2 11 13"/></>,
    check: <path d="m5 12 4 4L19 6"/>
    arrow: <path d="m9 18 6-6-6-6"/>
    plus: <path d="M12 5v14M5 12h14"/>
    google: <><path d="M21.4 12.2c0-.7-.1-1.4-.2-2H12v3.8h5.3a4.5 4.5 0 0 1-2 3v2.5h3.2c1.9-1.8 2.9-4.3 2.9-7.3Z"/><path d="M12 22c2.7 0 5-.9 6.6-2.4l-3.2-2.5c-.9.6-2 1-3.4 1-2.6 0-4.8-1.8-5.6-4.2H3.1v2.6A10 10 0 0 0 12 22Z"/><path d="M6.4 13.9a6 6 0 0 1 0-3.8V7.5H3.1a10 10 0 0 0 0 9l3.3-2.6Z"/><path d="M12 5.9c1.5 0 2.8.5 3.8 1.5l2.9-2.8A9.7 9.7 0 0 0 3.1 7.5l3.3 2.6C7.2 7.7 9.4 5.9 12 5.9Z"/></>,
    user: <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}

function Brand() {
  return <div className="brand"><span className="logo"><Icon name="spark" size={18}/></span><span>Planora</span></div>;
}

const seedTasks: Task[] = [
  { id: "US-014", title: "Créer un système de connexion", priority: "Élevée", points: 5, status: "done", owner: "ML" },
  { id: "US-018", title: "Parcourir les restaurants", priority: "Élevée", points: 5, status: "progress", owner: "AC" },
  { id: "US-021", title: "Configurer le paiement", priority: "Moyenne", points: 8, status: "backlog", owner: "JD" },
  { id: "US-006", title: "Créer le profil étudiant", priority: "Moyenne", points: 3, status: "review", owner: "ML" },
  { id: "US-002", title: "Initialiser l'application", priority: "Basse", points: 3, status: "done", owner: "AC" },
];

const questions = [
  { id: 1, title: "Délai du projet", text: "Quel est le délai souhaité ?", choices: ["1 mois", "3 mois", "6 mois", "Flexible"] },
  { id: 2, title: "Équipe", text: "Combien de développeurs seront disponibles ?", choices: ["1", "2", "3", "4", "5+"] },
  { id: 3, title: "Plateforme", text: "Sur quelle plateforme souhaitez-vous lancer le produit ?", choices: ["Web", "Mobile", "Web + Mobile"] },
];

function Progress({ board = false }: { board?: boolean }) {
  const steps = ["Projet", "Besoins", "Contraintes", "User Stories", "Backlog", "Scrum"];
  return <div className="progress-steps">{steps.map((step, index) => <div className={(board || index < 2) ? "complete" : index === 2 ? "active" : ""} key={step}><i>{(board || index < 2) ? <Icon name="check" size={10}/> : null}</i><span>{step}</span></div>)}</div>;
}

function ProjectChat() {
  const [started, setStarted] = useState(false);
  const [active, setActive] = useState<number | null>(null);
  const [answered, setAnswered] = useState<number[]>([]);
  const [input, setInput] = useState("");
  const submitIdea = () => { if (input.trim()) { setStarted(true); setInput(""); } };
  const answer = (id: number) => { setAnswered((items) => [...items, id]); setActive(null); };
  const remaining = questions.length - answered.length;

  return (
    <main className="onboarding">
      <header className="app-header"><Brand/><Progress/><button className="avatar-button"><Icon name="user" size={16}/></button></header>
      <section className="chat-stage">
        <div className="stage-title"><span className="ai-orb"><Icon name="spark" size={24}/></span><h1>Votre Scrum Master IA</h1><p>Décrivez votre projet. Je vais vous aider à le transformer en un plan Scrum structuré.</p></div>
        <div className="chat-thread">
          <div className="ai-line"><span><Icon name="spark" size={16}/></span><div><strong>Scrum Master IA</strong><p>{started ? "J'ai compris l'objectif de votre projet. Il me manque encore quelques informations avant de construire votre backlog." : "Bonjour. Décrivez-moi votre projet avec vos propres mots. Je vais ensuite vous poser quelques questions pour comprendre vos besoins."}</p></div></div>
          {started && <>
            <div className="user-bubble">Je veux créer une application de livraison de repas pensée pour les étudiants.</div>
            <section className="question-card">
              <div className="question-heading"><div><span>Informations à compléter</span><h2>{remaining} élément{remaining > 1 ? "s" : ""} restant{remaining > 1 ? "s" : ""}</h2></div><strong>{answered.length}/{questions.length}</strong></div>
              {questions.map((question) => {
                const done = answered.includes(question.id);
                return <article className={`${done ? "done" : ""} ${active === question.id ? "open" : ""}`} key={question.id}>
                  <div className="question-index">{done ? <Icon name="check" size={14}/> : `0${question.id}`}</div>
                  <div className="question-content"><h3>{question.title}</h3><p>{done ? "Information ajoutée au projet" : question.text}</p>
                    {active === question.id && <div className="quick-choices">{question.choices.map((choice) => <button key={choice} onClick={() => answer(question.id)}>{choice}</button>)}</div>}
                  </div>
                  {!done && active !== question.id && <button className="answer-button" onClick={() => setActive(question.id)}>Répondre</button>}
                </article>;
              })}
            </section>
            {remaining === 0 && <div className="ready-card"><Icon name="check"/><div><strong>Le projet est suffisamment défini</strong><p>Je peux maintenant générer les User Stories, le backlog et les premiers sprints.</p></div><button className="primary" onClick={() => {}}>Générer mon backlog<Icon name="arrow" size={16}/></button></div>}
          </>}
        </div>
        {!started && <div className="idea-examples"><span>Essayez par exemple</span><button onClick={() => setInput("Je veux créer une application de livraison de repas pour les étudiants.")}>Application de livraison étudiante</button><button onClick={() => setInput("Je souhaite lancer une plateforme de réservation pour indépendants.")}>Plateforme de réservation</button></div>}
        <div className="main-composer"><textarea value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submitIdea(); }}} placeholder="Décrivez votre projet..."/><button onClick={submitIdea}><Icon name="send" size={18}/></button></div>
        <p className="composer-note">Vos réponses restent modifiables à tout moment</p>
      </section>
    </main>
  );
}

function Generating() {
  return (
    <main className="generation">
      <div className="brand"><Icon name="spark" size={18}/><span>Planora</span></div>
      <section>
        <span className="generating-orb"><Icon name="spark" size={27}/></span>
        <p className="kicker">Construction de votre projet</p>
        <h1>Votre Scrum Master prépare le plan.</h1>
        <p>Nous transformons vos réponses en une organisation claire et réaliste.</p>
        <div className="generation-list">
          {["Analyse du projet", "Génération des User Stories", "Construction du backlog", "Priorisation Scrum", "Préparation du tableau"].map((item, i) => (
            <div className={i < 4 ? "done" : "loading"} key={item}>
              {i < 4 ? <Icon name="check" size={14}/> : <span/>}
              <strong>{item}</strong>
              <em>{i < 4 ? "Terminé" : "En cours"}</em>
            </div>
          ))}
        </div>
        <button className="primary" onClick={() => {}}>Afficher mon espace projet<Icon name="arrow" size={16}/></button>
      </section>
    </main>
  );
}

function KanbanBoard() {
  const [tasks, setTasks] = useState(seedTasks);
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("J'ai organisé le Sprint 1 autour de l'inscription et de la découverte des restaurants.");
  const points = useMemo(() => tasks.reduce((sum, task) => sum + task.points, 0), [tasks]);
  
  const move = (id: string, status: Status) => setTasks((all) => all.map((task) => task.id === id ? { ...task, status } : task));
  const send = () => {
    if (!message.trim()) return;
    if (message.toLowerCase().includes("paiement") || message.includes("US-021")) { 
      move("US-021", "backlog"); 
      setReply("C'est fait. J'ai déplacé US-021 — Configurer le paiement dans le Sprint 2."); 
    }
    else setReply("Cette tâche est prioritaire car elle débloque le parcours principal et trois autres tâches du Sprint 1.");
    setMessage("");
  };

  return (
    <main className="board-app">
      <header className="app-header">
        <Brand/>
        <div className="project-name">
          <span>Projet</span>
          <strong>Campus Eats</strong>
        </div>
        <button className="avatar-button"><Icon name="user" size={16}/></button>
      </header>
      
      <div className="final-layout">
        <section className="kanban-panel">
          <div className="kanban-title">
            <div>
              <span className="blue-kicker">Sprint 1 · Actif</span>
              <h1>Expérience de commande initiale</h1>
              <p>Permettre aux étudiants de découvrir un restaurant et de créer leur compte.</p>
            </div>
            <button className="primary"><Icon name="plus" size={16}/>Nouvelle tâche</button>
          </div>
          
          <div className="sprint-bar">
            <div>
              <strong>3 / {points} points</strong>
              <span>Progression du sprint</span>
            </div>
            <div className="bar"><i/></div>
            <span>28 juin</span>
          </div>
          
          <div className="kanban-grid">
            {columns.map((column) => { 
              const items = tasks.filter((task) => task.status === column.id); 
              return (
                <section 
                  className="kanban-column" 
                  key={column.id} 
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => move(e.dataTransfer.getData("task"), column.id)}
                >
                  <header>
                    <div>
                      <i className={column.id}/>
                      <strong>{column.label}</strong>
                      <span>{items.length}</span>
                    </div>
                    <button><Icon name="plus" size={14}/></button>
                  </header>
                  <div className="cards">
                    {items.map((task) => (
                      <article 
                        className="task" 
                        draggable 
                        onDragStart={(e) => e.dataTransfer.setData("task", task.id)} 
                        key={task.id}
                      >
                        <span>{task.id}</span>
                        <h3>{task.title}</h3>
                        <div>
                          <em className={task.priority === "Élevée" ? "high" : ""}>{task.priority}</em>
                          <small>{task.points} points</small>
                          <i>{task.owner}</i>
                        </div>
                      </article>
                    ))}
                    {items.length === 0 && <div className="empty-drop">Déposer ici</div>}
                  </div>
                </section>
              );
            })}
          </div>
        </section>
        
        <aside className="board-chat">
          <header>
            <span className="ai-orb small"><Icon name="spark" size={18}/></span>
            <div>
              <h2>Scrum Master IA</h2>
              <p>Connecté au tableau</p>
            </div>
            <i/>
          </header>
          
          <div className="chat-context">
            <span>Contexte actuel</span>
            <strong>Sprint 1 · 5 tâches · 24 points</strong>
          </div>
          
          <div className="board-thread">
            <div className="ai-line compact">
              <span><Icon name="spark" size={14}/></span>
              <div>
                <strong>Scrum Master IA</strong>
                <p>{reply}</p>
              </div>
            </div>
            <div className="user-bubble small">Pourquoi cette tâche est-elle prioritaire ?</div>
          </div>
          
          <div className="board-composer">
            <div className="suggestions">
              <button onClick={() => setMessage("Pourquoi cette tâche est prioritaire ?")}>
                Expliquer une priorité
              </button>
              <button onClick={() => setMessage("Déplace le paiement au Sprint 2")}>
                Réorganiser le sprint
              </button>
            </div>
            <div>
              <textarea 
                value={message} 
                onChange={(e) => setMessage(e.target.value)} 
                onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); send(); }}} 
                placeholder="Demandez une modification..."
              />
              <button onClick={send}><Icon name="send" size={17}/></button>
            </div>
            <p><Icon name="spark" size={12}/>L'IA peut modifier directement le tableau</p>
          </div>
        </aside>
      </div>
    </main>
  );
}

export default function BoardPage() {
  // Pour l'instant, on affiche le board directement
  // Plus tard, on peut gérer les différents écrans
  return <KanbanBoard />;
}

export { ProjectChat, Generating, KanbanBoard };
