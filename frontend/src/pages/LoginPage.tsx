import { useState, type FormEvent } from "react";
import { getCurrentUser, login } from "../services/api";

function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  
  const [user, setUser] = useState<{
   email: string;
   is_superuser: boolean;
  } | null>(null); 

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      const data = await login(email, password);

      localStorage.setItem("access_token", data.access_token);
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      console.error(error);
    }
  }
  return (
    <main>
      <h2>Login</h2>

      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>

        <div>
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>

        <button type="submit">Login</button>
      </form>
      {user && (
        <section>
          <h3>Authenticated User</h3>
          <p>Email: {user.email}</p>
          <p>
            Admin: {user.is_superuser ? "Yes" : "No"}
          </p>
        </section>
      )}
    </main>
  );
}

export default LoginPage;