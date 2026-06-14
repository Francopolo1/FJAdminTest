import { useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import axios from "axios";
import { confirmPasswordReset } from "../lib/authApi";

export function ResetPasswordPage() {
  const { uid, token } = useParams<{ uid: string; token: string }>();

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [info, setInfo] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (!uid || !token) {
      setError("Invalid or expired reset link.");
      return;
    }

    setIsSubmitting(true);
    try {
      const { detail } = await confirmPasswordReset(uid, token, password);
      setInfo(detail);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data) {
        const data = err.response.data as Record<string, string[] | string>;
        const firstError = Object.values(data).flat()[0];
        setError(typeof firstError === "string" ? firstError : "Unable to reset password.");
      } else {
        setError("Unable to reset password. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <div className="sidebar-logo-icon">
            <svg viewBox="0 0 24 24" style={{ width: 18, height: 18, fill: "none", stroke: "#fff", strokeWidth: 2 }}>
              <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><path d="M14 17.5h7M17.5 14v7" />
            </svg>
          </div>
          <span>FJ<em>ADMIN</em></span>
        </div>

        <div className="card">
          <div className="card-body">
            {error && <div className="alert alert-error">{error}</div>}
            {info && <div className="alert alert-success">{info}</div>}

            {!info && (
              <form className="login-form" onSubmit={(e) => void handleSubmit(e)}>
                <label className="field-label" htmlFor="password">New password</label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  className="input"
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />

                <label className="field-label" htmlFor="confirm_password">Confirm new password</label>
                <input
                  id="confirm_password"
                  name="confirm_password"
                  type="password"
                  className="input"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />

                <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                  {isSubmitting ? "Resetting…" : "Reset password"}
                </button>
              </form>
            )}

            <div className="login-form-footer">
              <Link to="/login">Back to sign in</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
