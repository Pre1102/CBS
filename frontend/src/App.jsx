import React, { useState, useEffect } from 'react';
import {
  fetchDepartmentResources,
  createBooking,
  fetchBookings,
  cancelBooking
} from './services/api';
import ConcurrentConflictDemo from './components/ConcurrentConflictDemo';

function App() {
  const [activeTab, setActiveTab] = useState('home'); // 'home' | 'resources' | 'bookings' | 'conflict'

  // Common State loaded directly from SQLite
  const [allResources, setAllResources] = useState({ CSE: [], IT: [], 'E&TC': [] });
  const [selectedDeptFilter, setSelectedDeptFilter] = useState('ALL');

  // Booking Form State (starts empty, uses placeholders for manual entry)
  const [bookingDept, setBookingDept] = useState('CSE');
  const [bookingResourceId, setBookingResourceId] = useState('');
  const [bookingDate, setBookingDate] = useState('');
  const [bookingStartTime, setBookingStartTime] = useState('');
  const [bookingEndTime, setBookingEndTime] = useState('');
  const [bookingUserName, setBookingUserName] = useState('');
  const [bookingAlert, setBookingAlert] = useState(null); // { type: 'success'|'error', text: '' }

  // Active Bookings List State from SQLite
  const [activeBookingsDept, setActiveBookingsDept] = useState('CSE');
  const [bookingsList, setBookingsList] = useState([]);

  // Load all resources from SQLite via Backend APIs
  const loadAllResources = async () => {
    const cse = await fetchDepartmentResources('CSE');
    const it = await fetchDepartmentResources('IT');
    const entc = await fetchDepartmentResources('E&TC');
    setAllResources({ CSE: cse, IT: it, 'E&TC': entc });
  };

  // Load bookings from SQLite via Backend APIs
  const loadBookingsForDept = async (dept) => {
    const list = await fetchBookings(dept);
    setBookingsList(list);
  };

  useEffect(() => {
    loadAllResources();
  }, []);

  useEffect(() => {
    loadBookingsForDept(activeBookingsDept);
  }, [activeBookingsDept]);

  // Navigate & Pre-select Resource for Booking
  const handleQuickBook = (dept, resId) => {
    setBookingDept(dept);
    if (resId) setBookingResourceId(String(resId));
    setActiveTab('bookings');
  };

  // Submit Booking Form to Backend/SQLite
  const handleCreateBooking = async (e) => {
    e.preventDefault();
    setBookingAlert(null);

    // Validate resource selection
    if (!bookingResourceId) {
      setBookingAlert({ type: 'error', text: 'Please select a target resource from the dropdown.' });
      return;
    }

    if (!bookingUserName.trim() || !bookingDate || !bookingStartTime || !bookingEndTime) {
      setBookingAlert({ type: 'error', text: 'Please fill in all booking details.' });
      return;
    }

    if (bookingStartTime >= bookingEndTime) {
      setBookingAlert({ type: 'error', text: 'Invalid time bounds: Start time must be strictly before end time.' });
      return;
    }

    const payload = {
      resource_id: Number(bookingResourceId),
      booked_by: bookingUserName,
      department: bookingDept,
      booking_date: bookingDate,
      start_time: bookingStartTime,
      end_time: bookingEndTime,
      purpose: "Campus Resource Reservation"
    };

    const res = await createBooking(bookingDept, payload);
    if (res.success) {
      setBookingAlert({
        type: 'success',
        text: `Booking confirmed successfully! Saved to ${bookingDept} database with Booking ID #${res.data.id}`
      });
      // Clear form inputs after successful SQLite persistence
      setBookingUserName('');
      setBookingDate('');
      setBookingStartTime('');
      setBookingEndTime('');
      setBookingResourceId('');
      loadBookingsForDept(activeBookingsDept);
      loadAllResources();
    } else {
      const errDetail = res.error || '';
      setBookingAlert({
        type: 'error',
        text: (errDetail.includes('400') || errDetail.includes('conflict') || errDetail.includes('already has an overlapping booking'))
          ? 'Resource unavailable: This resource is already booked for the selected time.'
          : `Booking failed: ${errDetail}`
      });
    }
  };


  // Cancel Booking in Backend/SQLite
  const handleCancelBooking = async (bookingId) => {
    const res = await cancelBooking(activeBookingsDept, bookingId);
    if (res.success) {
      loadBookingsForDept(activeBookingsDept);
      loadAllResources();
    } else {
      alert(`Cancel failed: ${res.error}`);
    }
  };

  // Helper to gather flat array of resources across departments
  const getFlatResources = () => {
    if (selectedDeptFilter === 'ALL') {
      return [
        ...allResources.CSE.map(r => ({ ...r, dept: 'CSE' })),
        ...allResources.IT.map(r => ({ ...r, dept: 'IT' })),
        ...allResources['E&TC'].map(r => ({ ...r, dept: 'E&TC' }))
      ];
    }
    return (allResources[selectedDeptFilter] || []).map(r => ({ ...r, dept: selectedDeptFilter }));
  };

  // Helper to resolve resource name from resource_id
  const getResourceNameById = (dept, resId) => {
    const list = allResources[dept] || [];
    const found = list.find(r => r.id === resId);
    return found ? found.name : `Resource #${resId}`;
  };

  return (
    <div className="app-root">
      {/* Top Application Header */}
      <header className="app-header">
        <div className="brand-section">
          <span className="brand-title">Campus Resource Booking</span>
        </div>

        <nav className="nav-tabs">
          <button
            className={`nav-btn ${activeTab === 'home' ? 'active' : ''}`}
            onClick={() => setActiveTab('home')}
          >
            Home
          </button>
          <button
            className={`nav-btn ${activeTab === 'resources' ? 'active' : ''}`}
            onClick={() => setActiveTab('resources')}
          >
            Resources
          </button>
          <button
            className={`nav-btn ${activeTab === 'bookings' ? 'active' : ''}`}
            onClick={() => setActiveTab('bookings')}
          >
            Bookings
          </button>
          <button
            className={`nav-btn ${activeTab === 'conflict' ? 'active' : ''}`}
            style={activeTab === 'conflict' ? { borderBottom: '2px solid #2563eb', color: '#1e3a8a', fontWeight: 700 } : {}}
            onClick={() => setActiveTab('conflict')}
          >
            ⚡ Conflict Demo
          </button>
        </nav>
      </header>

      {/* Main Content Area */}
      <main className="container">
        {/* ==================================================================== */}
        {/* TAB 1: HOME PAGE                                                     */}
        {/* ==================================================================== */}
        {activeTab === 'home' && (
          <section className="tab-page">
            <div className="hero-banner">
              <h2>Campus Resource Booking</h2>
              <p>Find and reserve shared campus resources easily.</p>
            </div>

            <h3 className="section-title">Departments Overview</h3>
            <div className="dept-grid">
              {['CSE', 'IT', 'E&TC'].map((dept) => (
                <div key={dept} className="dept-card">
                  <div className="dept-card-header">
                    <h3>{dept} Department</h3>
                  </div>
                  <p>{allResources[dept] ? allResources[dept].length : 0} shared resources registered</p>
                </div>
              ))}
            </div>

            <h3 className="section-title">Featured Campus Resources</h3>
            <div className="cards-grid">
              {getFlatResources().slice(0, 6).map((res) => (
                <div key={`${res.dept}-${res.id}`} className="res-card">
                  <div>
                    <div className="res-card-top">
                      <div className="res-name">{res.name}</div>
                      <span className="res-badge">{res.dept}</span>
                    </div>
                    <div className="res-meta">
                      <div><strong>Type:</strong> {res.resource_type}</div>
                      <div><strong>Location:</strong> {res.location}</div>
                      <div><strong>Capacity:</strong> {res.capacity || 'N/A'} seats</div>
                      <div>
                        <strong>Status:</strong>{' '}
                        <span style={{ color: res.is_available ? 'var(--status-online)' : 'var(--status-offline)', fontWeight: 600 }}>
                          {res.is_available ? 'Available' : 'Unavailable'}
                        </span>
                      </div>
                    </div>
                  </div>
                  <button
                    className="btn-book-now"
                    onClick={() => handleQuickBook(res.dept, res.id)}
                  >
                    Book Now
                  </button>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ==================================================================== */}
        {/* TAB 2: RESOURCES PAGE                                                */}
        {/* ==================================================================== */}
        {activeTab === 'resources' && (
          <section className="tab-page">
            <h2 className="section-title">Campus Resources Inventory</h2>
            
            <div className="filter-bar">
              {['ALL', 'CSE', 'IT', 'E&TC'].map((dept) => (
                <button
                  key={dept}
                  className={`filter-btn ${selectedDeptFilter === dept ? 'active' : ''}`}
                  onClick={() => setSelectedDeptFilter(dept)}
                >
                  {dept === 'ALL' ? 'All Departments' : `${dept} Department`}
                </button>
              ))}
            </div>

            <div className="table-card">
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Department</th>
                    <th>Resource Name</th>
                    <th>Type</th>
                    <th>Location</th>
                    <th>Capacity</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {getFlatResources().map((res) => (
                    <tr key={`${res.dept}-${res.id}`}>
                      <td><span className="res-badge">{res.dept}</span></td>
                      <td><strong>{res.name}</strong></td>
                      <td>{res.resource_type}</td>
                      <td>{res.location}</td>
                      <td>{res.capacity}</td>
                      <td style={{ color: res.is_available ? 'var(--status-online)' : 'var(--status-offline)', fontWeight: 600 }}>
                        {res.is_available ? 'Available' : 'Unavailable'}
                      </td>
                      <td>
                        <button
                          className="filter-btn active"
                          style={{ padding: '0.25rem 0.6rem', fontSize: '0.78rem' }}
                          onClick={() => handleQuickBook(res.dept, res.id)}
                        >
                          View / Book
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* ==================================================================== */}
        {/* TAB 3: BOOKINGS PAGE                                                 */}
        {/* ==================================================================== */}
        {activeTab === 'bookings' && (
          <section className="tab-page">
            <h2 className="section-title">Resource Booking & Reservations</h2>

            {bookingAlert && (
              <div className={`alert-box alert-${bookingAlert.type}`}>
                {bookingAlert.text}
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '2rem' }}>
              {/* Left Column: Create Booking Form */}
              <div className="form-card">
                <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', fontWeight: 600 }}>Reserve a Resource</h3>
                <form onSubmit={handleCreateBooking}>
                  <div className="form-group">
                    <label>Target Department</label>
                    <select
                      className="form-control"
                      value={bookingDept}
                      onChange={(e) => {
                        setBookingDept(e.target.value);
                        setBookingResourceId('');
                      }}
                    >
                      <option value="CSE">CSE Department</option>
                      <option value="IT">IT Department</option>
                      <option value="E&TC">E&TC Department</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Resource Name</label>
                    <select
                      className="form-control"
                      value={bookingResourceId}
                      onChange={(e) => setBookingResourceId(e.target.value)}
                    >
                      <option value="">Select Resource...</option>
                      {(allResources[bookingDept] || []).map(r => (
                        <option key={r.id} value={r.id}>{r.name} ({r.resource_type})</option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Requester Name / Identifier</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="e.g. Student User / Rahul"
                      value={bookingUserName}
                      onChange={(e) => setBookingUserName(e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Date</label>
                    <input
                      type="date"
                      className="form-control"
                      value={bookingDate}
                      onChange={(e) => setBookingDate(e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label>Start Time</label>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="10:00"
                        value={bookingStartTime}
                        onChange={(e) => setBookingStartTime(e.target.value)}
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label>End Time</label>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="12:00"
                        value={bookingEndTime}
                        onChange={(e) => setBookingEndTime(e.target.value)}
                        required
                      />
                    </div>
                  </div>

                  <button type="submit" className="btn-book-now" style={{ marginTop: '0.5rem' }}>
                    Book Resource
                  </button>
                </form>
              </div>

              {/* Right Column: Existing Bookings from SQLite */}
              <div className="table-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Active Bookings</h3>
                  <div className="filter-bar" style={{ margin: 0 }}>
                    {['CSE', 'IT', 'E&TC'].map(d => (
                      <button
                        key={d}
                        className={`filter-btn ${activeBookingsDept === d ? 'active' : ''}`}
                        style={{ padding: '0.2rem 0.5rem', fontSize: '0.78rem' }}
                        onClick={() => setActiveBookingsDept(d)}
                      >
                        {d}
                      </button>
                    ))}
                  </div>
                </div>

                {bookingsList.filter(b => b.status === 'CONFIRMED').length === 0 ? (
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', padding: '1rem 0' }}>
                    No active bookings yet. Create your first reservation.
                  </p>
                ) : (
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Resource</th>
                        <th>User</th>
                        <th>Date</th>
                        <th>Time</th>
                        <th>Status</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bookingsList.filter(b => b.status === 'CONFIRMED').map(b => (
                        <tr key={b.id}>
                          <td>#{b.id}</td>
                          <td><strong>{getResourceNameById(activeBookingsDept, b.resource_id)}</strong></td>
                          <td>{b.booked_by || b.user_name || 'User'}</td>
                          <td>{b.booking_date}</td>

                          <td>{b.start_time} - {b.end_time}</td>
                          <td>
                            <span style={{ color: b.status === 'CONFIRMED' ? 'var(--status-online)' : 'var(--text-muted)', fontWeight: 600 }}>
                              {b.status}
                            </span>
                          </td>
                          <td>
                            {b.status === 'CONFIRMED' && (
                              <button
                                className="btn-cancel"
                                onClick={() => handleCancelBooking(b.id)}
                              >
                                Cancel
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </section>
        )}

        {/* ==================================================================== */}
        {/* TAB 4: CONCURRENT CONFLICT SIMULATION DEMO                           */}
        {/* ==================================================================== */}
        {activeTab === 'conflict' && (
          <ConcurrentConflictDemo />
        )}
      </main>

      {/* Application Footer */}
      <footer className="app-footer">
        <div>Distributed Campus Resource Booking System</div>
        <div>Department Nodes: CSE • IT • E&TC</div>
      </footer>
    </div>
  );
}

export default App;
