import {
  Box,
  Button,
  Container,
  Stack,
  Typography,
  useTheme,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export const LandingPage = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { tryItNow } = useAuth();

  const handleTryItNow = async () => {
    try {
      await tryItNow();
      navigate("/app/dashboard");
    } catch {
      navigate("/auth/login");
    }
  };

  const handleLogin = () => {
    navigate("/auth/login");
  };

  const handleRegister = () => {
    navigate("/auth/register");
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
        <Stack spacing={4} sx={{ textAlign: "center" }}>
          <Box>
            <Typography
              variant="h1"
              sx={{
                fontSize: { xs: "2.5rem", sm: "3.5rem" },
                fontWeight: 700,
                mb: 2,
              }}
            >
              Ergo Labs: Advisor
            </Typography>
            <Typography
              variant="body1"
              sx={{
                fontSize: "1.1rem",
                color: "text.secondary",
              }}
            >
              Create, review, and collaborate on scientific documents with
              support from a community-led Advisor.
            </Typography>
          </Box>

          <Stack spacing={2} sx={{ mt: 4 }}>
            <Button
              variant="contained"
              size="large"
              onClick={handleTryItNow}
              sx={{
                py: 1.5,
                fontSize: "1rem",
                background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
              }}
            >
              Try it Now
            </Button>

            <Stack direction="row" spacing={2}>
              <Button
                variant="outlined"
                size="large"
                onClick={handleLogin}
                sx={{
                  flex: 1,
                  py: 1.5,
                  fontSize: "1rem",
                }}
              >
                Login
              </Button>
              <Button
                variant="outlined"
                size="large"
                onClick={handleRegister}
                sx={{
                  flex: 1,
                  py: 1.5,
                  fontSize: "1rem",
                }}
              >
                Register
              </Button>
            </Stack>
          </Stack>

          <Typography
            variant="body2"
            sx={{
              color: "text.secondary",
              mt: 4,
            }}
          >
            No account needed to try it out. Your documents are automatically
            saved.
          </Typography>
        </Stack>
      </Container>
    </Box>
  );
};
