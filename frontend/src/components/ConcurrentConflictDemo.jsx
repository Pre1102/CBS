import React, { useState, useEffect } from 'react';
import { fetchPresetResources, simulateConcurrentConflict } from '../services/api';

export default function ConcurrentConflictDemo() {
  const [deptA, setDeptA] = useState('CSE');
  const [deptB, setDeptB] = useState('IT');
  const [resourceId, setResourceId] = useState('SHARED-SEMINAR-HALL');
  const [customResourceName, setCustomResourceName] = useState('Campus Shared Seminar Hall');
  const [bookingDate, setBookingDate] = useState('2026-09-10');
  const [startTime, setStartTime] = useState('10:00');
  const [endTime, setEndTime] = useState('12:00');
  const [requesterA, setRequesterA] = useState('Prof. Sharma (CSE)');
  const [requesterB, setRequesterB] = useState('Dr. Kulkarni (IT)');
  const [staggerDelayMs, setStaggerDelayMs] = useState(0);

  const [presetResources, setPresetResources] = useState([]);
  const [isCustomResource, setIsCustomResource] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [simulationResult, setSimulationResult] = useState(null);
  const [errorAlert, setErrorAlert] = useState(null);
  const [traceFilter, setTraceFilter] = useState('ALL');

  useEffect(() => {
    async function loadPresets() {
      const presets = await fetchPresetResources();
      if (presets && presets.length > 0) {
        setPresetResources(presets);
        setResourceId(presets[0].id);
        setCustomResourceName(presets[0].name);
      }
    }
    loadPresets();
  }, []);

  const handlePairSelection = (a, b) => {
    setDeptA(a);
    setDeptB(b);
    setRequesterA(`Prof. ${a} Lead`);
    setRequesterB(`Dr. ${b} Lead`);
  };

  const handleResourceChange = (e) => {
    const val = e.target.value;
    if (val === '__CUSTOM__') {
      setIsCustomResource(true);
      setResourceId('CUSTOM-SHARED-LAB');
      setCustomResourceName('Custom Shared Research Facility');
    } else {
      setIsCustomResource(false);
      setResourceId(val);
      const found = presetResources.find((r) => r.id === val);
      if (found) {
        setCustomResourceName(found.name);
      }
    }
  };

  const handleRunSimulation = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorAlert(null);
    setSimulationResult(null);

    const payload = {
      dept_a: deptA,
      dept_b: deptB,
      resource_id: resourceId,
      resource_name: customResourceName,
      booking_date: bookingDate,
      start_time: startTime,
      end_time: endTime,
      requester_a: requesterA,
      requester_b: requesterB,
      stagger_delay_ms: Number(staggerDelayMs)
    };

    const res = await simulateConcurrentConflict(payload);
    setIsLoading(false);

    if (res.success) {
      setSimulationResult(res.data);
    } else {
      setErrorAlert(res.error || 'Failed to execute concurrent simulation');
    }
  };

  const getFilteredEvents = () => {
    if (!simulationResult || !simulationResult.event_trace) return [];
    if (traceFilter === 'ALL') return simulationResult.event_trace;
    return simulationResult.event_trace.filter((ev) => ev.node === traceFilter);
  };

  return (
    <div className="tab-page conflict-demo-container">
      {/* Header Banner */}
      <div className="hero-banner" style={{ background: 'linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%)', color: '#fff' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <span style={{ fontSize: '1.8rem' }}>⚡</span>
          <h2 style={{ margin: 0, color: '#ffffff' }}>Distributed Concurrency & Conflict Demo</h2>
        </div>
        <p style={{ color: '#cbd5e1', maxWidth: '800px', fontSize: '0.95rem' }}>
          Simulate real concurrent access by two independent department nodes competing for the exact same shared campus resource.
          Observe <strong>Lamport Logical Clock progression</strong>, deterministic priority ordering <code>(timestamp, node_id)</code>,
          and <strong>Ricart–Agrawala mutual exclusion</strong> strictly preventing double-booking in SQLite.
        </p>
      </div>

      {errorAlert && (
        <div className="alert-box alert-error" style={{ margin: '1rem 0' }}>
          {errorAlert}
        </div>
      )}

      {/* Main Grid: Form Controls (Left) & Simulation Dashboard (Right) */}
      <div className="sim-layout-grid">
        {/* LEFT PANEL: CONFIGURATION */}
        <div className="form-card" style={{ height: 'fit-content' }}>
          <h3 style={{ fontSize: '1.15rem', marginBottom: '1.25rem', fontWeight: 700, color: 'var(--primary-accent)' }}>
            1. Simulation Parameters
          </h3>

          <form onSubmit={handleRunSimulation}>
            {/* Department Pair Quick Select */}
            <div className="form-group">
              <label>Select Competing Department Pair</label>
              <div className="quick-pair-buttons">
                <button
                  type="button"
                  className={`pair-btn ${deptA === 'CSE' && deptB === 'IT' ? 'active' : ''}`}
                  onClick={() => handlePairSelection('CSE', 'IT')}
                >
                  CSE vs IT
                </button>
                <button
                  type="button"
                  className={`pair-btn ${deptA === 'IT' && deptB === 'E&TC' ? 'active' : ''}`}
                  onClick={() => handlePairSelection('IT', 'E&TC')}
                >
                  IT vs E&TC
                </button>
                <button
                  type="button"
                  className={`pair-btn ${deptA === 'CSE' && deptB === 'E&TC' ? 'active' : ''}`}
                  onClick={() => handlePairSelection('CSE', 'E&TC')}
                >
                  CSE vs E&TC
                </button>
              </div>
            </div>

            {/* Custom Dept Selectors */}
            <div className="form-row">
              <div className="form-group">
                <label>Department A (First Node)</label>
                <select
                  className="form-control"
                  value={deptA}
                  onChange={(e) => setDeptA(e.target.value)}
                >
                  <option value="CSE">CSE Node (50151 / 50051)</option>
                  <option value="IT">IT Node (50152 / 50052)</option>
                  <option value="E&TC">E&TC Node (50153 / 50053)</option>
                </select>
              </div>
              <div className="form-group">
                <label>Department B (Second Node)</label>
                <select
                  className="form-control"
                  value={deptB}
                  onChange={(e) => setDeptB(e.target.value)}
                >
                  <option value="IT">IT Node (50152 / 50052)</option>
                  <option value="CSE">CSE Node (50151 / 50051)</option>
                  <option value="E&TC">E&TC Node (50153 / 50053)</option>
                </select>
              </div>
            </div>

            {/* Resource Selection */}
            <div className="form-group">
              <label>Target Shared Campus Resource</label>
              <select
                className="form-control"
                value={isCustomResource ? '__CUSTOM__' : resourceId}
                onChange={handleResourceChange}
              >
                {presetResources.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name} ({r.resource_type})
                  </option>
                ))}
                <option value="__CUSTOM__">+ Custom Resource Identifier...</option>
              </select>
            </div>

            {isCustomResource && (
              <div className="form-row">
                <div className="form-group">
                  <label>Resource Identifier</label>
                  <input
                    type="text"
                    className="form-control"
                    value={resourceId}
                    onChange={(e) => setResourceId(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Resource Display Name</label>
                  <input
                    type="text"
                    className="form-control"
                    value={customResourceName}
                    onChange={(e) => setCustomResourceName(e.target.value)}
                    required
                  />
                </div>
              </div>
            )}

            {/* Date & Time Selection */}
            <div className="form-row">
              <div className="form-group">
                <label>Simulation Date</label>
                <input
                  type="date"
                  className="form-control"
                  value={bookingDate}
                  onChange={(e) => setBookingDate(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Start Time</label>
                <input
                  type="text"
                  className="form-control"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  placeholder="10:00"
                  required
                />
              </div>
              <div className="form-group">
                <label>End Time</label>
                <input
                  type="text"
                  className="form-control"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  placeholder="12:00"
                  required
                />
              </div>
            </div>

            {/* Requester Names */}
            <div className="form-row">
              <div className="form-group">
                <label>{deptA} Requester Name</label>
                <input
                  type="text"
                  className="form-control"
                  value={requesterA}
                  onChange={(e) => setRequesterA(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>{deptB} Requester Name</label>
                <input
                  type="text"
                  className="form-control"
                  value={requesterB}
                  onChange={(e) => setRequesterB(e.target.value)}
                  required
                />
              </div>
            </div>

            {/* Launch Stagger Delay Slider */}
            <div className="form-group" style={{ marginTop: '0.5rem', background: '#f8fafc', padding: '0.85rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                <label style={{ margin: 0, fontWeight: 600, fontSize: '0.88rem' }}>
                  Launch Delay Stagger ({deptB} offset):
                </label>
                <span className="stagger-badge">
                  {staggerDelayMs === 0 ? '0 ms (Simultaneous)' : `+${staggerDelayMs} ms delay`}
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="500"
                step="10"
                value={staggerDelayMs}
                onChange={(e) => setStaggerDelayMs(Number(e.target.value))}
                style={{ width: '100%', cursor: 'pointer' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                <span>0 ms (Tie-Breaker Demo)</span>
                <span>250 ms</span>
                <span>500 ms (Staggered Demo)</span>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="btn-book-now"
              disabled={isLoading || deptA === deptB}
              style={{
                marginTop: '1rem',
                padding: '0.75rem',
                fontSize: '1rem',
                fontWeight: 700,
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem'
              }}
            >
              {isLoading ? (
                <>⏳ Running Concurrent gRPC Simulation...</>
              ) : (
                <>▶ Run Simultaneous Simulation</>
              )}
            </button>
            {deptA === deptB && (
              <small style={{ color: 'var(--status-offline)', display: 'block', marginTop: '0.4rem', textAlign: 'center' }}>
                Please select two distinct departments to simulate conflict.
              </small>
            )}
          </form>
        </div>

        {/* RIGHT PANEL: LIVE VISUALIZATION & RESULTS */}
        <div className="sim-results-panel">
          {!simulationResult && !isLoading && (
            <div className="table-card" style={{ padding: '3rem 2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏛️ ⚔️ 🏛️</div>
              <h3 style={{ color: 'var(--text-main)', marginBottom: '0.5rem' }}>Ready for Simulation</h3>
              <p style={{ maxWidth: '480px', margin: '0 auto', fontSize: '0.9rem' }}>
                Select participating department nodes and launch delay, then click <strong>"Run Simultaneous Simulation"</strong> to execute
                real concurrent gRPC requests, Lamport clock updates, and SQLite conflict resolution.
              </p>
            </div>
          )}

          {isLoading && (
            <div className="table-card" style={{ padding: '3rem 2rem', textAlign: 'center' }}>
              <div className="spinner" style={{ margin: '0 auto 1.5rem auto' }}></div>
              <h3 style={{ color: 'var(--primary-accent)' }}>Simulating Distributed Concurrency...</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                Exchanging gRPC RequestResourceAccess RPCs between {deptA} and {deptB} nodes...
              </p>
            </div>
          )}

          {simulationResult && (
            <div className="sim-outcome-container">
              {/* TOP SUMMARY OUTCOME BANNER */}
              <div className="sim-outcome-banner">
                <div className="winner-box">
                  <div className="outcome-tag tag-winner">🏆 Access Granted (Critical Section Held)</div>
                  <h4 style={{ margin: '0.4rem 0', fontSize: '1.25rem', color: '#166534' }}>
                    {simulationResult.winner_department} Department Won Reservation
                  </h4>
                  <p style={{ margin: 0, fontSize: '0.88rem', color: '#15803d' }}>
                    <strong>Booking ID #{simulationResult.winner_booking_id}</strong> confirmed for <em>{simulationResult.winner_requester}</em> on {simulationResult.booking_date} ({simulationResult.time_slot}).
                  </p>
                </div>

                <div className="loser-box">
                  <div className="outcome-tag tag-loser">🛡️ Double-Booking Strictly Prevented</div>
                  <h4 style={{ margin: '0.4rem 0', fontSize: '1.1rem', color: '#991b1b' }}>
                    {simulationResult.loser_department} Department Booking Blocked
                  </h4>
                  <p style={{ margin: 0, fontSize: '0.85rem', color: '#b91c1c' }}>
                    {simulationResult.loser_reason}
                  </p>
                </div>
              </div>

              {/* SIDE-BY-SIDE DEPARTMENT NODE CARDS */}
              <div className="nodes-side-by-side">
                {/* NODE A CARD */}
                <div className={`node-sim-card ${simulationResult.winner_department === deptA ? 'card-winner' : 'card-loser'}`}>
                  <div className="node-sim-card-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span className="res-badge">{deptA}</span>
                      <strong style={{ fontSize: '1.05rem' }}>{deptA} Department Node</strong>
                    </div>
                    {simulationResult.winner_department === deptA ? (
                      <span className="badge-outcome winner">WINNER</span>
                    ) : (
                      <span className="badge-outcome prevented">CONFLICT BLOCKED</span>
                    )}
                  </div>

                  <div className="node-stat-grid">
                    <div className="stat-item">
                      <span className="stat-label">Initial Clock:</span>
                      <strong className="clock-num">{simulationResult.lamport_clocks[deptA]?.initial}</strong>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Request Timestamp (T):</span>
                      <strong className="clock-num highlight">{simulationResult.lamport_clocks[deptA]?.request_timestamp}</strong>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Final Clock:</span>
                      <strong className="clock-num">{simulationResult.lamport_clocks[deptA]?.final}</strong>
                    </div>
                  </div>

                  <div className="node-flow-state">
                    <span className="flow-step done">IDLE</span>
                    <span className="flow-arrow">→</span>
                    <span className="flow-step done">REQUESTING</span>
                    <span className="flow-arrow">→</span>
                    <span className={`flow-step ${simulationResult.winner_department === deptA ? 'done-success' : 'done-wait'}`}>
                      {simulationResult.winner_department === deptA ? 'HELD (Access)' : 'WAITING (Deferred)'}
                    </span>
                    <span className="flow-arrow">→</span>
                    <span className="flow-step done">RELEASED</span>
                  </div>
                </div>

                {/* NODE B CARD */}
                <div className={`node-sim-card ${simulationResult.winner_department === deptB ? 'card-winner' : 'card-loser'}`}>
                  <div className="node-sim-card-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span className="res-badge">{deptB}</span>
                      <strong style={{ fontSize: '1.05rem' }}>{deptB} Department Node</strong>
                    </div>
                    {simulationResult.winner_department === deptB ? (
                      <span className="badge-outcome winner">WINNER</span>
                    ) : (
                      <span className="badge-outcome prevented">CONFLICT BLOCKED</span>
                    )}
                  </div>

                  <div className="node-stat-grid">
                    <div className="stat-item">
                      <span className="stat-label">Initial Clock:</span>
                      <strong className="clock-num">{simulationResult.lamport_clocks[deptB]?.initial}</strong>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Request Timestamp (T):</span>
                      <strong className="clock-num highlight">{simulationResult.lamport_clocks[deptB]?.request_timestamp}</strong>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Final Clock:</span>
                      <strong className="clock-num">{simulationResult.lamport_clocks[deptB]?.final}</strong>
                    </div>
                  </div>

                  <div className="node-flow-state">
                    <span className="flow-step done">IDLE</span>
                    <span className="flow-arrow">→</span>
                    <span className="flow-step done">REQUESTING</span>
                    <span className="flow-arrow">→</span>
                    <span className={`flow-step ${simulationResult.winner_department === deptB ? 'done-success' : 'done-wait'}`}>
                      {simulationResult.winner_department === deptB ? 'HELD (Access)' : 'WAITING (Deferred)'}
                    </span>
                    <span className="flow-arrow">→</span>
                    <span className="flow-step done">RELEASED</span>
                  </div>
                </div>
              </div>

              {/* RICART-AGRAWALA ORDERING RULE BADGE */}
              <div className="ordering-rule-card">
                <span style={{ fontSize: '1.2rem' }}>⚖️</span>
                <div>
                  <strong>Ricart–Agrawala Logical Priority Order: </strong>
                  <code>{simulationResult.priority_rule}</code>
                  <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                    Lower timestamp wins priority. If timestamps are identical, deterministic alphanumeric tie-breaking <code>({deptA} vs {deptB})</code> breaks the tie.
                  </p>
                </div>
              </div>

              {/* CHRONOLOGICAL EVENT TRACE */}
              <div className="table-card" style={{ marginTop: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>
                    Chronological Execution Trace ({getFilteredEvents().length} Events)
                  </h3>

                  <div className="filter-bar" style={{ margin: 0 }}>
                    <button
                      className={`filter-btn ${traceFilter === 'ALL' ? 'active' : ''}`}
                      style={{ padding: '0.2rem 0.6rem', fontSize: '0.78rem' }}
                      onClick={() => setTraceFilter('ALL')}
                    >
                      All Events
                    </button>
                    <button
                      className={`filter-btn ${traceFilter === deptA ? 'active' : ''}`}
                      style={{ padding: '0.2rem 0.6rem', fontSize: '0.78rem' }}
                      onClick={() => setTraceFilter(deptA)}
                    >
                      {deptA} Events
                    </button>
                    <button
                      className={`filter-btn ${traceFilter === deptB ? 'active' : ''}`}
                      style={{ padding: '0.2rem 0.6rem', fontSize: '0.78rem' }}
                      onClick={() => setTraceFilter(deptB)}
                    >
                      {deptB} Events
                    </button>
                  </div>
                </div>

                <div className="event-timeline-list">
                  {getFilteredEvents().map((ev, idx) => (
                    <div key={idx} className={`timeline-entry event-${ev.event_type.toLowerCase()}`}>
                      <div className="timeline-time">+{ev.elapsed_ms} ms</div>
                      <div className="timeline-badge-node">
                        <span className="res-badge" style={{ fontSize: '0.7rem' }}>{ev.node}</span>
                      </div>
                      <div className="timeline-content">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                          <span className={`event-type-pill pill-${ev.event_type.toLowerCase()}`}>
                            {ev.event_type}
                          </span>
                          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                            Clock: {ev.lamport_clock_before} → <strong>{ev.lamport_clock_after}</strong>
                          </span>
                        </div>
                        <div className="timeline-message">{ev.message}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* VIVA & CONCEPT EXPLAINER BOX */}
      <div className="theory-box" style={{ marginTop: '2rem' }}>
        <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--primary-accent)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span>📚</span> Distributed Systems Concepts Demonstrated in this Simulation
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem', fontSize: '0.88rem' }}>
          <div>
            <strong>1. Lamport Logical Clocks:</strong>
            <p style={{ color: 'var(--text-muted)', margin: '0.2rem 0 0 0' }}>
              Tick rule increments clock before local request generation (<code>L = L + 1</code>). Receive rule updates clock upon gRPC message arrival (<code>L = max(L, T_recv) + 1</code>).
            </p>
          </div>
          <div>
            <strong>2. Ricart–Agrawala Mutual Exclusion:</strong>
            <p style={{ color: 'var(--text-muted)', margin: '0.2rem 0 0 0' }}>
              Requests are ordered by <code>(timestamp, node_name)</code>. The node with lower timestamp enters critical section first, while peer defers its reply.
            </p>
          </div>
          <div>
            <strong>3. Double-Booking Prevention:</strong>
            <p style={{ color: 'var(--text-muted)', margin: '0.2rem 0 0 0' }}>
              Mutual exclusion serializes the concurrent attempts. The winner commits the SQLite record first; when the deferred node executes, SQLite detects the overlapping time slot and rejects the duplicate.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
