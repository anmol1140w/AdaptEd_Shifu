import { AuthProvider } from "./AuthProvider";
import { PhaseOneApp } from "../features/auth/PhaseOneApp";

export default function App(){
  return <AuthProvider>
    <PhaseOneApp />
  </AuthProvider>
}