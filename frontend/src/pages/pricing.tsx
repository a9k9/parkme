import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiPricingRulesList } from "@/api/generated/api/api";

export function PricingPage() {
  const pricingQuery = useQuery({
    queryKey: ["pricing-rules"],
    queryFn: () => apiPricingRulesList(),
    staleTime: 60_000,
  });

  const rules = pricingQuery.data?.data?.results ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Pricing</h1>
        <p className="text-sm text-muted-foreground">
          Current rate plans across the network.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {rules.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>Pricing rules</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              {pricingQuery.isLoading
                ? "Loading pricing rules..."
                : "No pricing rules available."}
            </CardContent>
          </Card>
        ) : (
          rules.map((rule) => (
            <Card key={rule.id}>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  {rule.name}
                  <Badge variant={rule.is_active ? "secondary" : "outline"}>
                    {rule.is_active ? "Active" : "Inactive"}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-3xl font-semibold">
                  {rule.strategy ?? "Flat"}
                </p>
                <p className="text-sm text-muted-foreground">
                  Facility: {rule.facility_name}
                </p>
                {rule.free_minutes ? (
                  <p className="text-sm text-muted-foreground">
                    Free minutes: {rule.free_minutes}
                  </p>
                ) : null}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
