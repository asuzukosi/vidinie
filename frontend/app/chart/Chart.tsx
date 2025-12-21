import { SiteHeader } from "@/app/chart/SiteHeader";
import { SectionCards } from "@/app/chart/SectionCards";
import { ChartAreaInteractive } from "@/app/chart/ChartAreaInteractive";
import { DataTable } from "@/app/chart/DataTable";
import data from "@/app/chart/data.json";

export function Chart() {
    return (
        <div>
            <SiteHeader />
        <div className="flex flex-1 flex-col">
          <div className="@container/main flex flex-1 flex-col gap-2">
            <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
              <SectionCards />
              <div className="px-4 lg:px-6">
                <ChartAreaInteractive />
              </div>
              <DataTable data={data} />
            </div>
          </div>
        </div>
        </div>
    )
}