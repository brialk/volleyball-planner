// Every request to the Flask backend goes through this file, so URLs, JSON
// handling and error messages are written once.

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// AuthContext registers a function here. It runs when the server says
// "please log in" (for example after the session expires).
let onUnauthorized = () => {};
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

const AUTH_PATHS = ["/login", "/signup", "/check_session"];

async function request(path, { method = "GET", body } = {}) {
  let response;
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("Cannot reach the server. Check your connection.", 0);
  }

  if (response.status === 204) return null;

  let data = null;
  try {
    data = await response.json();
  } catch {
    // The body was not JSON (for example the proxy could not reach Flask).
  }

  if (!response.ok) {
    if (response.status === 401 && !AUTH_PATHS.includes(path)) onUnauthorized();
    if (!data?.error && response.status >= 500) {
      throw new ApiError("The server is not responding. Make sure the Flask backend is running on port 5555.", response.status);
    }
    throw new ApiError(data?.error || `Request failed (${response.status}).`, response.status);
  }

  return data;
}

function queryString(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) search.set(key, value);
  });
  const text = search.toString();
  return text ? `?${text}` : "";
}

export const api = {
  // auth
  checkSession: () => request("/check_session"),
  signup: (username, password) => request("/signup", { method: "POST", body: { username, password } }),
  login: (username, password) => request("/login", { method: "POST", body: { username, password } }),
  logout: () => request("/logout", { method: "DELETE" }),

  // drills
  getDrillOptions: () => request("/drill-options"),
  getDrills: (filters) => request(`/drills${queryString(filters)}`),
  createDrill: (drill) => request("/drills", { method: "POST", body: drill }),
  updateDrill: (id, changes) => request(`/drills/${id}`, { method: "PATCH", body: changes }),
  deleteDrill: (id) => request(`/drills/${id}`, { method: "DELETE" }),

  // plans
  getPlans: () => request("/plans"),
  getPlan: (id) => request(`/plans/${id}`),
  createPlan: (plan) => request("/plans", { method: "POST", body: plan }),
  updatePlan: (id, changes) => request(`/plans/${id}`, { method: "PATCH", body: changes }),
  deletePlan: (id) => request(`/plans/${id}`, { method: "DELETE" }),

  // drills inside a plan
  addPlanItem: (planId, item) => request(`/plans/${planId}/items`, { method: "POST", body: item }),
  updatePlanItem: (planId, itemId, changes) =>
    request(`/plans/${planId}/items/${itemId}`, { method: "PATCH", body: changes }),
  deletePlanItem: (planId, itemId) => request(`/plans/${planId}/items/${itemId}`, { method: "DELETE" }),
  reorderPlanItems: (planId, itemIds) =>
    request(`/plans/${planId}/items/order`, { method: "PUT", body: { item_ids: itemIds } }),
};
