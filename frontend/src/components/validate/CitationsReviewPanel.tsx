import { Box, Typography, Stack, LinearProgress } from "@mui/material";
import { ValidationResult } from "../../types";

interface CitationsReviewPanelProps {
  result: ValidationResult | null;
}

export function CitationsReviewPanel({ result }: CitationsReviewPanelProps) {
  const papers: any[] = (result as any)?.related_papers ?? [];

  return (
    <Box sx={{ p: 2, display: "flex", flexDirection: "column", gap: 2 }}>
      <Typography variant="subtitle2" fontWeight={600}>
        Related Papers ({papers.length})
      </Typography>
      {papers.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          No related papers data available. The librarian agent scores papers
          during the citations step.
        </Typography>
      ) : (
        <Stack spacing={2}>
          {papers.map((paper: any, i: number) => {
            const relevancy =
              paper.relevancy_score ?? paper.relevancy ?? 0;
            const convergence =
              paper.convergence_score ?? paper.convergence ?? 0;
            const convergencePositive = convergence >= 0;

            return (
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
                  {paper.title}
                </Typography>
                {(paper.venue || paper.year) && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    display="block"
                    gutterBottom
                  >
                    {[paper.venue, paper.year].filter(Boolean).join(" · ")}
                  </Typography>
                )}
                {paper.authors && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    display="block"
                    gutterBottom
                  >
                    {paper.authors}
                  </Typography>
                )}

                {/* Relevancy bar */}
                <Box sx={{ mb: 1 }}>
                  <Stack
                    direction="row"
                    justifyContent="space-between"
                    sx={{ mb: 0.25 }}
                  >
                    <Typography variant="caption">Relevancy</Typography>
                    <Typography variant="caption" fontWeight={700}>
                      {relevancy.toFixed(2)}
                    </Typography>
                  </Stack>
                  <LinearProgress
                    variant="determinate"
                    value={relevancy * 100}
                    sx={{ height: 4, borderRadius: 2 }}
                    color="primary"
                  />
                </Box>

                {/* Convergence bar */}
                <Box sx={{ mb: 1 }}>
                  <Stack
                    direction="row"
                    justifyContent="space-between"
                    sx={{ mb: 0.25 }}
                  >
                    <Typography variant="caption">Convergence</Typography>
                    <Typography
                      variant="caption"
                      fontWeight={700}
                      color={
                        convergencePositive ? "success.main" : "error.main"
                      }
                    >
                      {convergencePositive ? "+" : ""}
                      {convergence.toFixed(2)}
                    </Typography>
                  </Stack>
                  <LinearProgress
                    variant="determinate"
                    value={Math.abs(convergence) * 100}
                    sx={{ height: 4, borderRadius: 2 }}
                    color={convergencePositive ? "success" : "error"}
                  />
                </Box>

                {/* Agent reasoning / context */}
                {(paper.relevancy_reasoning || paper.context) && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    display="block"
                    sx={{ mt: 0.5, fontStyle: "italic" }}
                  >
                    {paper.relevancy_reasoning || paper.context}
                  </Typography>
                )}
                {paper.convergence_reasoning && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    display="block"
                    sx={{ mt: 0.25, fontStyle: "italic" }}
                  >
                    {paper.convergence_reasoning}
                  </Typography>
                )}
              </Box>
            );
          })}
        </Stack>
      )}
    </Box>
  );
}
