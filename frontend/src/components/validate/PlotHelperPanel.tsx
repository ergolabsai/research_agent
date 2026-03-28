import {
  Box,
  Typography,
  Stack,
  Divider,
  alpha,
  useTheme,
} from "@mui/material";
import {
  CheckCircle as CheckIcon,
  Cancel as RejectIcon,
} from "@mui/icons-material";
import { ValidationResult } from "../../types";

interface PlotHelperPanelProps {
  result: ValidationResult | null;
}

export function PlotHelperPanel({ result }: PlotHelperPanelProps) {
  const theme = useTheme();

  // Collect all figure validations across all step validations
  const allFigures = result
    ? Object.values(result.step_validations).flatMap(
        (v: any) => v.figure_validations ?? [],
      )
    : [];

  return (
    <Box sx={{ p: 2, display: "flex", flexDirection: "column", gap: 2 }}>
      {/* Decorative trend comparison chart */}
      <Box>
        <Typography variant="subtitle2" gutterBottom fontWeight={600}>
          Trend Comparison
        </Typography>
        <Stack direction="row" spacing={1}>
          <Box
            sx={{
              flex: 1,
              p: 1.5,
              borderRadius: 1,
              border: 1,
              borderColor: "divider",
            }}
          >
            <Typography
              variant="caption"
              color="text.secondary"
              display="block"
              gutterBottom
            >
              True
            </Typography>
            <svg
              viewBox="0 0 200 80"
              style={{ width: "100%", height: 56 }}
              aria-label="true plot"
            >
              <polyline
                fill="none"
                stroke={theme.palette.primary.main}
                strokeWidth="2.5"
                strokeLinejoin="round"
                points="8,65 30,56 55,46 80,34 100,24 120,20 145,30 168,40 190,44"
              />
            </svg>
          </Box>
          <Box
            sx={{
              flex: 1,
              p: 1.5,
              borderRadius: 1,
              border: 1,
              borderColor: "divider",
              bgcolor: alpha(theme.palette.warning.main, 0.05),
            }}
          >
            <Typography
              variant="caption"
              color="text.secondary"
              display="block"
              gutterBottom
            >
              Predicted
            </Typography>
            <svg
              viewBox="0 0 200 80"
              style={{ width: "100%", height: 56 }}
              aria-label="predicted plot"
            >
              <polyline
                fill="none"
                stroke={theme.palette.warning.main}
                strokeWidth="2.5"
                strokeLinejoin="round"
                points="8,66 30,60 55,52 80,44 100,38 120,36 145,38 168,42 190,43"
              />
            </svg>
          </Box>
        </Stack>
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ mt: 0.5, display: "block" }}
        >
          Inflection delay detected around epoch 36 vs. predicted epoch 42.
        </Typography>
      </Box>

      <Divider />

      {/* Figure validations from results */}
      <Box>
        <Typography variant="subtitle2" gutterBottom fontWeight={600}>
          Figure Validations
        </Typography>
        {allFigures.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            No figure validation data available.
          </Typography>
        ) : (
          <Stack spacing={1.5}>
            {allFigures.map((fig: any, i: number) => (
              <Box
                key={i}
                sx={{
                  p: 1.5,
                  borderRadius: 1,
                  border: 1,
                  borderColor: "divider",
                }}
              >
                <Typography variant="body2" fontWeight={600} gutterBottom>
                  {fig.figure_name}
                </Typography>
                {(fig.validity?.confirmations ?? []).map(
                  (c: string, ci: number) => (
                    <Stack
                      key={`conf-${ci}`}
                      direction="row"
                      spacing={0.75}
                      alignItems="flex-start"
                      sx={{ mb: 0.5 }}
                    >
                      <CheckIcon
                        color="success"
                        sx={{ fontSize: 14, mt: 0.3, flexShrink: 0 }}
                      />
                      <Typography variant="caption">{c}</Typography>
                    </Stack>
                  ),
                )}
                {(fig.validity?.contradictions ?? []).map(
                  (c: string, ci: number) => (
                    <Stack
                      key={`contra-${ci}`}
                      direction="row"
                      spacing={0.75}
                      alignItems="flex-start"
                      sx={{ mb: 0.5 }}
                    >
                      <RejectIcon
                        color="error"
                        sx={{ fontSize: 14, mt: 0.3, flexShrink: 0 }}
                      />
                      <Typography variant="caption">{c}</Typography>
                    </Stack>
                  ),
                )}
                {!(fig.validity?.confirmations?.length ?? 0) &&
                  !(fig.validity?.contradictions?.length ?? 0) && (
                    <Typography variant="caption" color="text.secondary">
                      No confirmation/contradiction detail available.
                    </Typography>
                  )}
              </Box>
            ))}
          </Stack>
        )}
      </Box>
    </Box>
  );
}
