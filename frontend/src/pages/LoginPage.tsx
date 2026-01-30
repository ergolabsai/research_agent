import React, { useState } from "react";
import {
  Container,
  Box,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  useTheme,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export const LoginPage = () => {
  const navigate = useNavigate();
  const { login, loading, error, user } = useAuth();
  const theme = useTheme();

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");

  React.useEffect(() => {
    if (user) {
      navigate("/app/dashboard", { replace: true });
    }
  }, [user, navigate]);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(identifier, password);
      navigate("/app/dashboard");
    } catch {
      // Error is handled by context
      console.log("Login failed");
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: `linear-gradient(135deg, ${theme.palette.primary.main}40 0%, ${theme.palette.secondary.main}40 100%)`,
      }}
    >
      <Container maxWidth="sm">
        <Box
          sx={{
            p: 4,
            borderRadius: "16px",
            backgroundColor: theme.palette.background.paper,
            boxShadow: "0 20px 60px rgba(0, 0, 0, 0.15)",
          }}
        >
          <Typography
            variant="h2"
            sx={{
              mb: 1,
              fontWeight: 700,
              textAlign: "center",
            }}
          >
            Welcome Back
          </Typography>

          <Typography
            variant="body1"
            sx={{
              color: "text.secondary",
              textAlign: "center",
              mb: 3,
            }}
          >
            Enter your credentials to access your documents
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box
            component="form"
            onSubmit={handleLoginSubmit}
            sx={{ display: "flex", flexDirection: "column", gap: 2 }}
          >
            <TextField
              label="Email or Username"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              required
              fullWidth
              disabled={loading}
              size="small"
            />
            <TextField
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              fullWidth
              disabled={loading}
              size="small"
            />
            <Button
              type="submit"
              variant="contained"
              fullWidth
              disabled={loading}
              sx={{ mt: 2 }}
            >
              {loading ? <CircularProgress size={24} /> : "Login"}
            </Button>
          </Box>

          <Box sx={{ mt: 3, textAlign: "center" }}>
            <Typography variant="body2" sx={{ color: "text.secondary" }}>
              Don't have an account?{" "}
              <Button
                size="small"
                onClick={() => navigate("/auth/register")}
                sx={{ textTransform: "none" }}
              >
                Register here
              </Button>
            </Typography>
          </Box>

          <Box sx={{ mt: 2, textAlign: "center" }}>
            <Button
              size="small"
              onClick={() => navigate("/")}
              sx={{ textTransform: "none" }}
            >
              Back to home
            </Button>
          </Box>
        </Box>
      </Container>
    </Box>
  );
};
