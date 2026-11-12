import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Lock, ShieldCheck, ArrowRight, KeyRound, CheckCircle2 } from 'lucide-react';
import { Badge, Button, Card, Input, useToast } from '../../components/ui';
import { api } from '../../api';
import { User } from '../../types';

interface AuthPageProps {
  onAuthenticated: (user: User) => Promise<void> | void;
}

export const LoginPage: React.FC<AuthPageProps> = ({ onAuthenticated }) => {
  const navigate = useNavigate();
  const { notify } = useToast();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [mfaRequired, setMfaRequired] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const performLogin = async (loginEmail: string, loginPass: string, code?: string) => {
    setError(null);
    setLoading(true);
    try {
      const res = await api.login(loginEmail, loginPass, code);
      if (res.mfa_required) {
        setMfaRequired(true);
        notify('Enter your 6-digit authenticator code to complete sign in.', 'info');
        return;
      }
      if (res.user) {
        await onAuthenticated(res.user);
        notify('Signed in cleanly.', 'success');
        navigate('/app');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to sign in');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    performLogin(email, password, mfaRequired ? totpCode : undefined);
  };

  return (
    <div className="max-w-md mx-auto px-4 py-12 sm:py-16 space-y-6">
      <div className="text-center space-y-2">
        <Badge tone="forest">Authenticated Access</Badge>
        <h1 className="font-heading text-3xl font-extrabold text-[#202B43]">Sign in to NEXORA</h1>
        <p className="text-sm text-[#4E5D78]">Access your organization’s tenant-isolated workspace.</p>
      </div>

      <Card accent="forest" className="space-y-5">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Work Email"
            type="email"
            required
            autoComplete="email"
            placeholder="owner@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={mfaRequired}
          />
          <Input
            label="Password"
            type="password"
            required
            autoComplete="current-password"
            placeholder="••••••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={mfaRequired}
          />
          {mfaRequired && (
            <Input
              label="Authenticator Code (6 digits)"
              required
              inputMode="numeric"
              maxLength={6}
              placeholder="123456"
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value)}
            />
          )}

          {error && (
            <div className="p-3 rounded-xl bg-[#FEE2E2] border border-[#FECACA] text-xs font-medium text-[#991B1B]" role="alert">
              {error}
            </div>
          )}

          <div className="flex items-center justify-between text-xs">
            <Link to="/forgot-password" className="font-semibold text-[#3867E9] hover:underline">
              Forgot password?
            </Link>
            <Link to="/register" className="font-semibold text-[#3867E9] hover:underline">
              Create new workspace
            </Link>
          </div>

          <Button type="submit" className="w-full" size="lg" loading={loading} rightIcon={<ArrowRight className="w-4 h-4" />}>
            {mfaRequired ? 'Verify MFA & Enter Workspace' : 'Sign In'}
          </Button>
        </form>

        <div className="pt-4 border-t border-[#E2E8F4] space-y-2.5">
          <div className="text-[11px] font-bold uppercase tracking-wider text-[#4E5D78]">
            Fictional Sample Demo Accounts (Evaluation Sandbox)
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => {
                setEmail('alex@northbridge.example');
                setPassword('Owner@Nexora2026!');
                setMfaRequired(false);
              }}
            >
              Fill Sample Owner
            </Button>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => {
                setEmail('david.clerk@northbridge.example');
                setPassword('Clerk@Nexora2026!');
                setMfaRequired(false);
              }}
            >
              Fill Sample Staff
            </Button>
          </div>
          <p className="text-[11px] text-[#4E5D78]">
            Sample credentials prefill realistic fictional SME data (`Northbridge Distribution Co.`) using real PostgreSQL session cookies &amp; Argon2id hashing.
          </p>
        </div>
      </Card>
    </div>
  );
};

export const RegisterPage: React.FC<AuthPageProps> = ({ onAuthenticated }) => {
  const navigate = useNavigate();
  const { notify } = useToast();
  const [form, setForm] = useState({
    company_name: '',
    full_name: '',
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verifyNotice, setVerifyNotice] = useState<{ token?: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.registerWorkspace(form);
      await onAuthenticated(res.user);
      if (res.verification_token) {
        setVerifyNotice({ token: res.verification_token });
      }
      notify('Business workspace created successfully.', 'success');
      navigate('/app');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-12 sm:py-16 space-y-6">
      <div className="text-center space-y-2">
        <Badge tone="cobalt">New Organization Setup</Badge>
        <h1 className="font-heading text-3xl font-extrabold text-[#202B43]">Create your NEXORA workspace</h1>
        <p className="text-sm text-[#4E5D78]">Provisions an isolated multi-tenant workspace with owner permissions.</p>
      </div>

      <Card accent="cobalt" className="space-y-4">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Business / Workspace Name"
            required
            placeholder="Northbridge Hardware & Supply"
            value={form.company_name}
            onChange={(e) => setForm({ ...form, company_name: e.target.value })}
          />
          <Input
            label="Your Full Name"
            required
            placeholder="Elena Novak"
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          />
          <Input
            label="Work Email"
            type="email"
            required
            placeholder="elena@northbridge.example"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
          <Input
            label="Password (min 10 chars, upper/lower/number/symbol)"
            type="password"
            required
            minLength={10}
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
          {error && (
            <div className="p-3 rounded-xl bg-[#FEE2E2] border border-[#FECACA] text-xs font-medium text-[#991B1B]" role="alert">
              {error}
            </div>
          )}
          {verifyNotice?.token && (
            <div className="p-3 rounded-xl bg-[#EAF0FE] text-xs text-[#3867E9]">
              Verification token created: <code className="font-mono">{verifyNotice.token}</code>
            </div>
          )}
          <Button type="submit" className="w-full" size="lg" loading={loading}>
            Create Isolated Workspace
          </Button>
        </form>
        <div className="text-center text-xs text-[#4E5D78]">
          Already registered? <Link to="/login" className="font-semibold text-[#3867E9] underline">Sign in</Link>
        </div>
      </Card>
    </div>
  );
};

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sentResult, setSentResult] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.forgotPassword(email);
      setSentResult(res.dev_reset_token || 'SUBMITTED');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-12 sm:py-16">
      <Card accent="forest" className="space-y-4">
        <div className="flex items-center gap-2 text-[#3867E9]">
          <KeyRound className="w-5 h-5" />
          <h1 className="font-heading text-xl font-bold text-[#202B43]">Reset your password</h1>
        </div>
        {sentResult ? (
          <div className="space-y-3 text-sm text-[#4E5D78]">
            <p>If an active account matches that email, an expiring single-use reset link has been issued.</p>
            {sentResult !== 'SUBMITTED' && (
              <div className="p-3 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] text-xs">
                Local single-use reset link ready:{' '}
                <Link to={`/reset-password?token=${encodeURIComponent(sentResult)}`} className="font-mono font-bold text-[#3867E9] underline">
                  Open Reset Password
                </Link>
              </div>
            )}
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input label="Account Email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
            <Button type="submit" className="w-full" loading={loading}>Issue Expiring Reset Token</Button>
          </form>
        )}
      </Card>
    </div>
  );
};

export const ResetPasswordPage: React.FC = () => {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { notify } = useToast();
  const [token, setToken] = useState(params.get('token') || '');
  const [newPassword, setNewPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.resetPassword(token, newPassword);
      notify('Password updated cleanly. All older sessions revoked.', 'success');
      navigate('/login');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to reset password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-12 sm:py-16">
      <Card accent="forest" className="space-y-4">
        <div className="flex items-center gap-2 text-[#3867E9]">
          <Lock className="w-5 h-5" />
          <h1 className="font-heading text-xl font-bold text-[#202B43]">Set a new password</h1>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Single-use Reset Token" required value={token} onChange={(e) => setToken(e.target.value)} />
          <Input label="New Password" type="password" required minLength={10} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
          {error && <div className="p-3 rounded-xl bg-[#FEE2E2] text-xs text-[#991B1B]">{error}</div>}
          <Button type="submit" className="w-full" loading={loading}>Update Password</Button>
        </form>
      </Card>
    </div>
  );
};

export const VerifyEmailPage: React.FC = () => {
  const [params] = useSearchParams();
  const [token, setToken] = useState(params.get('token') || '');
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const verify = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.verifyEmail(token);
      setStatusMsg('Email verified cleanly.');
    } catch (err) {
      setStatusMsg(err instanceof Error ? err.message : 'Verification failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-12 sm:py-16">
      <Card accent="lime" className="space-y-4">
        <div className="flex items-center gap-2 text-[#3867E9]">
          <ShieldCheck className="w-5 h-5" />
          <h1 className="font-heading text-xl font-bold text-[#202B43]">Verify Work Email</h1>
        </div>
        <form onSubmit={verify} className="space-y-4">
          <Input label="Verification Token" required value={token} onChange={(e) => setToken(e.target.value)} />
          <Button type="submit" className="w-full" loading={loading}>Confirm Verification</Button>
        </form>
        {statusMsg && <p className="text-xs font-semibold text-[#3867E9]">{statusMsg}</p>}
      </Card>
    </div>
  );
};

export const AcceptInvitePage: React.FC<AuthPageProps> = ({ onAuthenticated }) => {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { notify } = useToast();
  const [token, setToken] = useState(params.get('token') || '');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleAccept = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.acceptInvitation({ token, full_name: fullName, password });
      await onAuthenticated(res.user);
      notify('Invitation accepted. Welcome to the workspace.', 'success');
      navigate('/app');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to accept invitation');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-12 sm:py-16">
      <Card accent="forest" className="space-y-4">
        <div className="flex items-center gap-2 text-[#3867E9]">
          <CheckCircle2 className="w-5 h-5" />
          <h1 className="font-heading text-xl font-bold text-[#202B43]">Join Invited Workspace</h1>
        </div>
        <form onSubmit={handleAccept} className="space-y-4">
          <Input label="Invitation Token" required value={token} onChange={(e) => setToken(e.target.value)} />
          <Input label="Your Full Name" required value={fullName} onChange={(e) => setFullName(e.target.value)} />
          <Input label="Set Strong Password" type="password" required minLength={10} value={password} onChange={(e) => setPassword(e.target.value)} />
          {error && <div className="p-3 rounded-xl bg-[#FEE2E2] text-xs text-[#991B1B]">{error}</div>}
          <Button type="submit" className="w-full" loading={loading}>Activate Membership</Button>
        </form>
      </Card>
    </div>
  );
};
