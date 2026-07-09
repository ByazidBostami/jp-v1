import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ui";
import Home from "./pages/Home";
import Jobs from "./pages/Jobs";
import JobDetail from "./pages/JobDetail";
import About from "./pages/About";
import Contact from "./pages/Contact";
import Login from "./pages/Login";
import Register from "./pages/Register";
import CandidateDash from "./pages/CandidateDash";
import EmployerDash from "./pages/EmployerDash";
import AdminDash from "./pages/AdminDash";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/jobs/:id" element={<JobDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/candidate" element={<ProtectedRoute role="candidate"><CandidateDash /></ProtectedRoute>} />
          <Route path="/employer" element={<ProtectedRoute role="employer"><EmployerDash /></ProtectedRoute>} />
          <Route path="/admin" element={<AdminGuard><AdminDash /></AdminGuard>} />
          <Route path="*" element={<Home />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

// admin, super_admin, verifier, interviewer all use the admin console
import { useAuth } from "./context/AuthContext";
import { Navigate } from "react-router-dom";
import { Spinner } from "./components/ui";
function AdminGuard({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div style={{ minHeight: "60vh" }}><Spinner /></div>;
  if (!user) return <Navigate to="/login?next=/admin" replace />;
  if (!["admin", "super_admin", "verifier", "interviewer"].includes(user.role)) return <Navigate to="/" replace />;
  return children;
}
