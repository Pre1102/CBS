const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

/**
 * Check health status of Gateway /api/health endpoint.
 */
export async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });
    if (response.ok) {
      const data = await response.json();
      return { online: true, data };
    }
    return { online: false };
  } catch {
    return { online: false };
  }
}

/**
 * Fetch health status of all department nodes via Gateway.
 */
export async function fetchDepartmentStatuses() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/departments/status`);
    if (response.ok) {
      return await response.json();
    }
    return { CSE: 'OFFLINE', IT: 'OFFLINE', 'E&TC': 'OFFLINE' };
  } catch {
    return { CSE: 'OFFLINE', IT: 'OFFLINE', 'E&TC': 'OFFLINE' };
  }
}

/**
 * Fetch resources belonging to a target department via Gateway.
 */
export async function fetchDepartmentResources(department) {
  try {
    const normalizedDepartment = department.toUpperCase().replace(/[^A-Z]/g, '');
    const deptKey = ['ENTC', 'ETC'].includes(normalizedDepartment)
      ? 'entc'
      : department.toLowerCase();
    const response = await fetch(`${API_BASE_URL}/api/departments/${deptKey}/resources`);
    if (response.ok) {
      return await response.json();
    }
    return [];
  } catch {
    return [];
  }
}

/**
 * Phase 3: Fetch remote department resources using gRPC Inter-Node RPC call via CSE node.
 */
export async function fetchRemoteResourcesViaGrpc(sourceDept = 'CSE', targetDept = 'IT') {
  try {
    const sourceKey = sourceDept.toLowerCase();
    const targetKey = targetDept === 'E&TC' ? 'entc' : targetDept.toLowerCase();
    const response = await fetch(`${API_BASE_URL}/api/departments/${sourceKey}/remote-resources/${targetKey}`);
    
    if (response.ok) {
      const data = await response.json();
      return { success: true, data };
    } else {
      const err = await response.json();
      return { success: false, error: err.detail || 'gRPC call failed' };
    }
  } catch (e) {
    return { success: false, error: 'Network error contacting Gateway/Node' };
  }
}

/**
 * Phase 4: Fetch coordination status for a department node.
 */
export async function fetchCoordinationStatus(department) {
  try {
    const deptKey = department === 'E&TC' ? 'entc' : department.toLowerCase();
    const response = await fetch(`${API_BASE_URL}/api/departments/${deptKey}/coordination/status`);
    if (response.ok) {
      return await response.json();
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Phase 4: Request access to a shared resource using Ricart-Agrawala mutual exclusion protocol.
 */
export async function requestSharedResource(department, resourceId = 'SHARED-SEMINAR-HALL') {
  try {
    const deptKey = department === 'E&TC' ? 'entc' : department.toLowerCase();
    const response = await fetch(`${API_BASE_URL}/api/departments/${deptKey}/coordination/request`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resource_id: resourceId })
    });
    const data = await response.json();
    if (response.ok) {
      return { success: true, data };
    } else {
      return { success: false, error: data.detail || 'Request failed' };
    }
  } catch (e) {
    return { success: false, error: 'Network error submitting request' };
  }
}

/**
 * Phase 4: Release access to a shared resource.
 */
export async function releaseSharedResource(department, resourceId = 'SHARED-SEMINAR-HALL') {
  try {
    const deptKey = department === 'E&TC' ? 'entc' : department.toLowerCase();
    const response = await fetch(`${API_BASE_URL}/api/departments/${deptKey}/coordination/release`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resource_id: resourceId })
    });
    const data = await response.json();
    if (response.ok) {
      return { success: true, data };
    } else {
      return { success: false, error: data.detail || 'Release failed' };
    }
  } catch (e) {
    return { success: false, error: 'Network error submitting release' };
  }
}

/**
 * Phase 5: Fetch fault-monitoring peer health status for a department node.
 */
export async function fetchFaultStatus(department) {
  try {
    const deptKey = department === 'E&TC' ? 'entc' : department.toLowerCase();
    const response = await fetch(`${API_BASE_URL}/api/departments/${deptKey}/fault-status`);
    if (response.ok) {
      return await response.json();
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Create a booking for a department resource via Gateway.
 */
export async function createBooking(department, bookingData) {
  try {
    const deptKey = department === 'E&TC' ? 'entc' : department.toLowerCase();
    const response = await fetch(`${API_BASE_URL}/api/departments/${deptKey}/bookings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bookingData)
    });
    const data = await response.json();
    if (response.ok) {
      return { success: true, data };
    } else {
      return { success: false, error: data.detail || 'Booking failed' };
    }
  } catch {
    return { success: false, error: 'Network error submitting booking' };
  }
}

/**
 * Fetch all bookings for a department via Gateway.
 */
export async function fetchBookings(department) {
  try {
    const deptKey = department === 'E&TC' ? 'entc' : department.toLowerCase();
    const response = await fetch(`${API_BASE_URL}/api/departments/${deptKey}/bookings`);
    if (response.ok) {
      return await response.json();
    }
    return [];
  } catch {
    return [];
  }
}

/**
 * Cancel an existing booking for a department via Gateway.
 */
export async function cancelBooking(department, bookingId) {
  try {
    const deptKey = department === 'E&TC' ? 'entc' : department.toLowerCase();
    const response = await fetch(`${API_BASE_URL}/api/departments/${deptKey}/bookings/${bookingId}/cancel`, {
      method: 'PUT'
    });
    const data = await response.json();
    if (response.ok) {
      return { success: true, data };
    } else {
      return { success: false, error: data.detail || 'Cancel failed' };
    }
  } catch {
    return { success: false, error: 'Network error cancelling booking' };
  }
}

/**
 * Fetch preset shared campus resources available for simulation.
 */
export async function fetchPresetResources() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/coordination/preset-resources`);
    if (response.ok) {
      return await response.json();
    }
    return [];
  } catch {
    return [];
  }
}

/**
 * Execute concurrent conflict simulation between two department nodes.
 */
export async function simulateConcurrentConflict(config) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/coordination/simulate-conflict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    const data = await response.json();
    if (response.ok) {
      return { success: true, data };
    } else {
      return { success: false, error: data.detail || 'Simulation execution failed' };
    }
  } catch (e) {
    return { success: false, error: 'Network error connecting to API Gateway' };
  }
}


