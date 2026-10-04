import React from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { ProtectedRoute } from "../App.jsx";
import { AuthProvider } from "../auth.jsx";
import { Empty, ErrorBox, ProbabilityBar, ReasonList, RiskBadge, StatCard } from "./ui.jsx";

describe("UI components", () => {
  it("renders risk badges with the risk level", () => {
    render(<RiskBadge level="HIGH" />);
    expect(screen.getByText("HIGH")).toHaveClass("badge-risk-high");
  });
  it("renders a stat card", () => {
    render(<StatCard label="Total shipments" value={63} />);
    expect(screen.getByText("Total shipments")).toBeInTheDocument();
    expect(screen.getByText("63")).toBeInTheDocument();
  });
  it("lists risk reasons and handles the empty case", () => {
    const { rerender } = render(<ReasonList reasons={["High traffic", "Rain conditions"]} />);
    expect(screen.getByText("High traffic")).toBeInTheDocument();
    rerender(<ReasonList reasons={[]} />);
    expect(screen.getByText(/No risk factors/)).toBeInTheDocument();
  });
  it("shows an error message and an empty state", () => {
    render(<><ErrorBox message="Boom" /><Empty title="Nothing" /></>);
    expect(screen.getByRole("alert")).toHaveTextContent("Boom");
    expect(screen.getByText("Nothing")).toBeInTheDocument();
  });
  it("renders the probability as a percentage", () => {
    render(<ProbabilityBar value={0.82} />);
    expect(screen.getByText("82%")).toBeInTheDocument();
  });
});

describe("ProtectedRoute", () => {
  it("redirects unauthenticated users away from protected content", () => {
    localStorage.clear();
    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <AuthProvider><ProtectedRoute><div>secret dashboard</div></ProtectedRoute></AuthProvider>
      </MemoryRouter>
    );
    expect(screen.queryByText("secret dashboard")).not.toBeInTheDocument();
  });
});
