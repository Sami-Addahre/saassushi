const objectives = [
  { title: 'Riduzione No-Show', desc: 'Caparra confirmatoria e promemoria automatici a 24h e 3h dall\'appuntamento.', icon: '01' },
  { title: 'Ottimizzazione Tavoli', desc: 'Lista d\'attesa intelligente che riempie i posti liberati dalle cancellazioni in tempo reale.', icon: '02' },
  { title: 'Aumento Ricavi', desc: 'Upsell automatico di aperitivi, dolci e sake subito dopo la conferma prenotazione.', icon: '03' },
  { title: 'Reputazione Online', desc: 'Richiesta feedback post-pasto e invito a recensioni su Google.', icon: '04' },
];

const phases = [
  {
    letter: 'A',
    title: 'Prenotazione e Verifica',
    desc: 'Il cliente indica nome, persone, data e fascia oraria. Il bot verifica disponibilità su database e Google Calendar. Se esaurito, entra in lista d\'attesa.',
  },
  {
    letter: 'B',
    title: 'Conferma e Upsell',
    desc: 'Dopo la conferma, il bot propone extra personalizzati con sconto esclusivo per aumentare il valore medio per cliente.',
  },
  {
    letter: 'C',
    title: 'Promemoria Attivi',
    desc: 'Notifiche T-24h con opzione cancellazione, T-3h con indicazioni stradali. Cancellazioni attivano la lista d\'attesa.',
  },
  {
    letter: 'D',
    title: 'Post-Pasto',
    desc: 'Tre ore dopo il pasto, richiesta di feedback e invito a lasciare recensioni pubbliche.',
  },
];

const stack = [
  { name: 'Telegram Bot', desc: 'Canale diretto con i clienti, interfaccia conversazionale guidata.' },
  { name: 'Google Calendar', desc: 'Sincronizzazione bidirezionale: ogni prenotazione diventa un evento visibile allo staff.' },
  { name: 'SQLite', desc: 'Database locale per prenotazioni, lista d\'attesa e promemoria schedulati.' },
  { name: 'Stripe', desc: 'Gestione caparre confirmatorie (integrazione pronta per produzione).' },
];

function IconTelegram() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z" />
    </svg>
  );
}

function IconCalendar() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="3" y="4" width="18" height="18" rx="2" />
      <path d="M16 2v4M8 2v4M3 10h18" strokeLinecap="round" />
    </svg>
  );
}

export default function App() {
  const botLink = import.meta.env.VITE_TELEGRAM_BOT || 'https://t.me/your_bot';

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <header className="relative overflow-hidden bg-ink text-paper">
        <div className="absolute inset-0 opacity-20">
          <div className="absolute -right-20 -top-20 h-96 w-96 rounded-full bg-crimson blur-3xl" />
          <div className="absolute -bottom-10 -left-10 h-64 w-64 rounded-full bg-gold blur-3xl opacity-40" />
        </div>

        <nav className="relative mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
          <span className="font-display text-2xl tracking-wide">SaaS Sushi</span>
          <a href={botLink} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 border border-paper/20 px-4 py-2 text-sm transition-colors hover:border-crimson hover:text-crimson">
            <IconTelegram /> Prova il Bot
          </a>
        </nav>

        <div className="relative mx-auto max-w-6xl px-6 pb-24 pt-16 md:pb-32 md:pt-24">
          <p className="animate-fade-up text-xs font-medium tracking-[0.3em] text-gold uppercase">Sistema di prenotazione intelligente</p>
          <h1 className="animate-fade-up stagger-1 mt-4 max-w-3xl font-display text-5xl leading-[1.1] md:text-7xl">
            Trasforma Telegram<br />nel tuo concierge
          </h1>
          <p className="animate-fade-up stagger-2 mt-6 max-w-xl text-base leading-relaxed text-paper/70 md:text-lg">
            Bot automatizzato per ristoranti sushi: prenotazioni, caparre, lista d'attesa, upsell e sincronizzazione Google Calendar — tutto in un unico flusso.
          </p>
          <div className="animate-fade-up stagger-3 mt-10 flex flex-wrap gap-4">
            <a href={botLink} target="_blank" rel="noopener noreferrer" className="bg-crimson px-8 py-4 text-sm font-medium tracking-wide text-white transition-colors hover:bg-crimson-dark">
              Apri il Bot Telegram
            </a>
            <a href="#flusso" className="border border-paper/30 px-8 py-4 text-sm font-medium tracking-wide transition-colors hover:border-paper">
              Scopri il flusso
            </a>
          </div>
        </div>
      </header>

      {/* Obiettivi */}
      <section className="mx-auto max-w-6xl px-6 py-20 md:py-28">
        <p className="text-xs tracking-[0.25em] text-muted uppercase">Obiettivi</p>
        <h2 className="mt-2 font-display text-4xl md:text-5xl">Cosa risolve il sistema</h2>
        <div className="mt-12 grid gap-6 md:grid-cols-2">
          {objectives.map((o) => (
            <div key={o.title} className="group border border-ink/10 p-8 transition-colors hover:border-crimson/30">
              <span className="font-display text-3xl text-crimson/40">{o.icon}</span>
              <h3 className="mt-4 font-display text-2xl">{o.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-muted">{o.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Flusso */}
      <section id="flusso" className="bg-ink text-paper">
        <div className="mx-auto max-w-6xl px-6 py-20 md:py-28">
          <p className="text-xs tracking-[0.25em] text-gold uppercase">Esperienza utente</p>
          <h2 className="mt-2 font-display text-4xl md:text-5xl">Il percorso in 4 fasi</h2>
          <div className="mt-12 space-y-0">
            {phases.map((p, i) => (
              <div key={p.letter} className={`grid gap-6 border-t border-paper/10 py-10 md:grid-cols-12 ${i === 0 ? 'border-t-0' : ''}`}>
                <div className="md:col-span-2">
                  <span className="font-display text-5xl text-crimson">{p.letter}</span>
                </div>
                <div className="md:col-span-10">
                  <h3 className="font-display text-2xl md:text-3xl">{p.title}</h3>
                  <p className="mt-3 max-w-2xl text-sm leading-relaxed text-paper/60 md:text-base">{p.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Integrazioni */}
      <section className="mx-auto max-w-6xl px-6 py-20 md:py-28">
        <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
          <div>
            <p className="text-xs tracking-[0.25em] text-muted uppercase">Integrazioni</p>
            <h2 className="mt-2 font-display text-4xl">Stack tecnico</h2>
            <p className="mt-4 text-muted leading-relaxed">
              Ogni prenotazione confermata viene sincronizzata automaticamente su Google Calendar. Lo staff visualizza tutto in tempo reale senza doppie digitazioni.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {stack.map((s) => (
              <div key={s.name} className="border border-ink/10 bg-white p-6">
                <h3 className="font-medium">{s.name}</h3>
                <p className="mt-2 text-sm text-muted">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-16 flex items-center gap-6 border border-ink/10 bg-white p-8 md:p-10">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center bg-ink text-paper">
            <IconCalendar />
          </div>
          <div>
            <h3 className="font-display text-2xl">Google Calendar collegato</h3>
            <p className="mt-2 text-sm text-muted">
              Configura un Service Account Google, condividi il calendario del ristorante e ogni prenotazione Telegram diventa un evento con promemoria integrati.
            </p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-ink/10 bg-paper">
        <div className="mx-auto max-w-6xl px-6 py-20 text-center md:py-24">
          <h2 className="font-display text-4xl md:text-5xl">Pronto a automatizzare?</h2>
          <p className="mx-auto mt-4 max-w-md text-muted">
            Avvia il bot Telegram e prova il flusso completo di prenotazione con sync calendario.
          </p>
          <a href={botLink} target="_blank" rel="noopener noreferrer" className="mt-8 inline-flex items-center gap-2 bg-crimson px-10 py-4 text-sm font-medium text-white transition-colors hover:bg-crimson-dark">
            <IconTelegram /> Prova il Bot
          </a>
        </div>
      </section>

      <footer className="border-t border-ink/10 px-6 py-8 text-center text-xs text-muted">
        SaaS Sushi — Sistema intelligente di prenotazione · Rovereto, Italia
      </footer>
    </div>
  );
}
