import { Paper, TableContainer } from "@material-ui/core";
import {
  AddBox,
  ArrowDownward,
  Check,
  ChevronLeft,
  ChevronRight,
  Clear,
  DeleteOutline,
  Edit,
  FilterList,
  FirstPage,
  LastPage,
  Remove,
  SaveAlt,
  Search,
  ViewColumn,
} from "@material-ui/icons";
import { Icons } from "material-table";
import MaterialTable, { MaterialTableProps } from "material-table";
import { forwardRef } from "react";
import React from "react";
import { responseInterface } from "swr";

const icons: Icons = {
  Add: forwardRef((props, ref) => <AddBox {...props} ref={ref} />),
  Check: forwardRef((props, ref) => <Check {...props} ref={ref} />),
  Clear: forwardRef((props, ref) => <Clear {...props} ref={ref} />),
  Delete: forwardRef((props, ref) => <DeleteOutline {...props} ref={ref} />),
  DetailPanel: forwardRef((props, ref) => <ChevronRight {...props} ref={ref} />),
  Edit: forwardRef((props, ref) => <Edit {...props} ref={ref} />),
  Export: forwardRef((props, ref) => <SaveAlt {...props} ref={ref} />),
  Filter: forwardRef((props, ref) => <FilterList {...props} ref={ref} />),
  FirstPage: forwardRef((props, ref) => <FirstPage {...props} ref={ref} />),
  LastPage: forwardRef((props, ref) => <LastPage {...props} ref={ref} />),
  NextPage: forwardRef((props, ref) => <ChevronRight {...props} ref={ref} />),
  PreviousPage: forwardRef((props, ref) => <ChevronLeft {...props} ref={ref} />),
  ResetSearch: forwardRef((props, ref) => <Clear {...props} ref={ref} />),
  Search: forwardRef((props, ref) => <Search {...props} ref={ref} />),
  SortArrow: forwardRef((props, ref) => <ArrowDownward {...props} ref={ref} />),
  ThirdStateCheck: forwardRef((props, ref) => <Remove {...props} ref={ref} />),
  ViewColumn: forwardRef((props, ref) => <ViewColumn {...props} ref={ref} />),
};

export interface SwrDataTableProps<DataType extends {}>
  extends Omit<MaterialTableProps<DataType>, "data" | "isLoading"> {
  /**
   * The return value of the `useSWR` hook for the corresponding endpoint
   */
  swr: responseInterface<DataType[], any>;
}

export function SwrDataTable<DataType extends {}>({ swr, ...props }: SwrDataTableProps<DataType>) {
  const { data, error } = swr;

  const isLoading = typeof data === "undefined" || typeof error !== "undefined";

  return (
    <MaterialTable
      icons={icons}
      isLoading={isLoading}
      data={data}
      {...props}
      components={{
        Container: (props) => (
          <TableContainer component={Paper} style={{ maxWidth: "100%" }} {...props} />
        ),
        ...props.components,
      }}
      options={{
        showTitle: false,
        draggable: false,
        search: true,
        searchFieldStyle: { maxWidth: "300px", alignSelf: "end" },
        actionsColumnIndex: -1,

        // TODO Implement pagination
        paging: false,
        paginationType: "stepped",
        minBodyHeight: 0,

        ...props.options,
      }}
    />
  );
}
