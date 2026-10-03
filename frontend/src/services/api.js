import axios from "axios";

const BASE_URL = "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("lifeflow_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function registerDonor(data) {
  return api.post("/auth/register/donor", data);
}

export function registerHospital(data) {
  return api.post("/auth/register/hospital", data);
}

export function registerReceiver(data) {
  return api.post("/auth/register/receiver", data);
}

export function loginDonor(email, password) {
  return api.post("/auth/login/donor", { email, password });
}

export function loginHospital(email, password) {
  return api.post("/auth/login/hospital", { email, password });
}

export function loginReceiver(email, password) {
  return api.post("/auth/login/receiver", { email, password });
}

export function loginAdmin(email, password) {
  return api.post("/auth/login/admin", { email, password });
}

export function loginStaff(email, password) {
  return api.post("/auth/login/staff", { email, password });
}

export function getMyDonorProfile() {
  return api.get("/donors/me");
}

export function getMyHospitalProfile() {
  return api.get("/hospitals/me");
}

export function getMyReceiverProfile() {
  return api.get("/receivers/me");
}

export function createHospitalRequest(data) {
  return api.post("/requests/hospital", data);
}

export function createReceiverRequest(data) {
  return api.post("/requests/receiver", data);
}

export function listBloodRequests() {
  return api.get("/requests");
}

export function getHospitalRequestHistory() {
  return api.get("/requests/hospital/history");
}

export function getReceiverRequestHistory() {
  return api.get("/requests/receiver/history");
}

export function getMatches(requestId) {
  return api.get(`/matching/${requestId}`);
}

export function acceptRequest(requestId, unitsDonated = 1) {
  return api.post(`/matching/${requestId}/accept`, { units_donated: unitsDonated });
}

export function logout() {
  localStorage.removeItem("lifeflow_token");
  localStorage.removeItem("lifeflow_role");
}

// ---- Donation history (full details of the other side, for every role) ----
export function getDonorDonationHistory() {
  return api.get("/donations/donor/history");
}
export function getHospitalDonationHistory() {
  return api.get("/donations/hospital/history");
}
export function getReceiverDonationHistory() {
  return api.get("/donations/receiver/history");
}

// ---- Notifications ----
export function getDonorNotifications() {
  return api.get("/notifications/donor");
}
export function getHospitalNotifications() {
  return api.get("/notifications/hospital");
}
export function getReceiverNotifications() {
  return api.get("/notifications/receiver");
}
export function markAllNotificationsRead(role) {
  return api.post(`/notifications/${role}/read-all`);
}

// ---- Ratings ----
export function rateDonor(donationId, stars, comment) {
  return api.post(`/ratings/${donationId}/rate-donor`, { stars, comment });
}
export function rateRequester(donationId, stars, comment) {
  return api.post(`/ratings/${donationId}/rate-requester`, { stars, comment });
}
export function getDonorRatings(donorId) {
  return api.get(`/ratings/donor/${donorId}`);
}

// ---- Blood inventory (hospital blood bank stock) ----
export function getMyInventory() {
  return api.get("/inventory/me");
}
export function updateMyInventory(item) {
  return api.put("/inventory/me", item);
}
export function getAllHospitalInventories() {
  return api.get("/inventory");
}

// ---- Donation camps / drives ----
export function createCamp(data) {
  return api.post("/camps", data);
}
export function listUpcomingCamps() {
  return api.get("/camps");
}
export function listMyCamps() {
  return api.get("/camps/mine");
}
export function listCampRsvps(campId) {
  return api.get(`/camps/${campId}/rsvps`);
}
export function rsvpToCamp(campId) {
  return api.post(`/camps/${campId}/rsvp`);
}
export function listMyRsvps() {
  return api.get("/camps/mine/rsvps");
}

// ---- Stats, badges, leaderboard ----
export function getDonorStats() {
  return api.get("/donors/me/stats");
}
export function getHospitalStats() {
  return api.get("/hospitals/me/stats");
}
export function getReceiverStats() {
  return api.get("/receivers/me/stats");
}
export function getDonorLeaderboard() {
  return api.get("/leaderboard/donors");
}

export function getPlatformStats() {
  return api.get("/stats/platform");
}

export function changeAdminPassword(current_password, new_password) {
  return api.post("/auth/admin/change-password", { current_password, new_password });
}

// ---- AI features ----
export function analyzeReport(report_text) {
  return api.post("/ai/analyze-report", { report_text });
}
export function getShortagePrediction() {
  return api.get("/ai/shortage-prediction");
}
export function getShortagePredictionAdmin(hospitalId) {
  return api.get(`/admin/hospital/${hospitalId}/shortage-prediction`);
}
export function sendChatMessage(message, slots) {
  return api.post("/ai/chat", { message, slots });
}

// ---- Admin: full visibility across every donor, hospital, and patient ----
export function getAllDonorsAdmin() {
  return api.get("/admin/donors");
}
export function getAllHospitalsAdmin() {
  return api.get("/admin/hospitals");
}
export function getAllReceiversAdmin() {
  return api.get("/admin/receivers");
}
export function getAllRequestsAdmin() {
  return api.get("/admin/requests");
}
export function getAllDonationsAdmin() {
  return api.get("/admin/donations");
}
export function getAllNotificationsAdmin() {
  return api.get("/admin/notifications");
}
export function getDonorHistoryAdmin(donorId) {
  return api.get(`/admin/donor/${donorId}/history`);
}
export function getHospitalHistoryAdmin(hospitalId) {
  return api.get(`/admin/hospital/${hospitalId}/history`);
}
export function getReceiverHistoryAdmin(receiverId) {
  return api.get(`/admin/receiver/${receiverId}/history`);
}
export function getAllStaffAdmin() {
  return api.get("/admin/staff");
}
export function getStaffHistoryAdmin(staffId) {
  return api.get(`/admin/staff/${staffId}/visitors`);
}

// ---- Hospital staff & shifts ----
export function createStaff(data) {
  return api.post("/staff", data);
}
export function listMyStaff() {
  return api.get("/staff");
}
export function removeStaff(staffId) {
  return api.delete(`/staff/${staffId}`);
}
export function getHospitalAllVisitors() {
  return api.get("/staff/hospital/visitors");
}
export function getMyStaffProfile() {
  return api.get("/staff/me");
}
export function logVisitor(data) {
  return api.post("/staff/visitors", data);
}
export function getMyVisitorEntries() {
  return api.get("/staff/visitors/mine");
}

export default api;
