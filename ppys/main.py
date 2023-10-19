import os
import re
import datetime
from decimal import Decimal
from pathlib import Path
from pypdf import PdfReader
from dotenv import load_dotenv
import pandas as pd
import tabula

import utils
from utils import MissingEnvVariables


APP_NAME = "ppys"
lg = utils.init_logger(APP_NAME)


AREA_DEDUCTIONS_BOX = [19.57, 51.15, 50.41, 100.0]
AREA_PAYTABLE_BOX = [19.57, 0.0, 50.41, 51.15]
AREA_PAYSUMMARY_BOX = [50.76, 50.66, 72.57, 100.0]
AREA_DATE_BOX = [6.68, 63.16, 15.83, 94.9]


class PdfObject:
    def __init__(self, filepath: Path) -> None:
        if not filepath.is_file():
            raise FileNotFoundError(f"{filepath=}")
        self.filepath = filepath
        self.raw_text = self.read_pdf(self.filepath)

    def read_pdf(self, filepat: Path) -> str:
        reader = PdfReader(filepat)
        text_list = []
        for i in range(len(reader.pages)):
            page = reader.pages[i]
            text_list.append(page.extract_text())
        return "\n\n".join(text_list)

    def get_paytable(self, area: list[float]) -> pd.DataFrame:
        dfs = tabula.io.read_pdf(
            self.filepath,
            pages=[1],
            pandas_options={"header": None},
            area=area,  # [top, left, bottom, right]
            relative_area=True,  # enables % from area argument
        )
        if not isinstance(dfs, list):
            dfs = [pd.DataFrame()]
        return dfs[0]

    def get_deductions_table(self, area: list[float]) -> pd.DataFrame:
        dfs = tabula.io.read_pdf(
            self.filepath,
            pages=[1],
            pandas_options={"header": None},
            area=area,  # [top, left, bottom, right]
            relative_area=True,  # enables % from area argument
        )
        if not isinstance(dfs, list):
            dfs = [pd.DataFrame()]
        return dfs[0]

    def get_pay_summary_table(self, area: list[float]) -> pd.DataFrame:
        dfs = tabula.io.read_pdf(
            self.filepath,
            pages=[1],
            pandas_options={"header": None},
            area=area,  # [top, left, bottom, right]
            relative_area=True,  # enables % from area argument
        )
        if not isinstance(dfs, list):
            dfs = [pd.DataFrame()]
        return dfs[0]

    def get_pay(self):
        descr_index_start = self.raw_text.find("DESCRIPTION")
        descr_index_end = self.raw_text[descr_index_start:].find("\n\n")
        if descr_index_end == -1:
            descr_index_end = self.raw_text[descr_index_start:].find("\n \n")
        if descr_index_end != -1:
            descr_index_end += descr_index_start

        pay_text = self.raw_text[descr_index_start:descr_index_end]
        # print(f"{self.raw_text[descr_index_start:]=}")
        print(f"{descr_index_start=}, {descr_index_end=}")
        print(f"{pay_text}")

        pay_numbers = []
        for line in pay_text.splitlines():
            try:
                pay_numbers.append(float(line.replace(",", "")))
            except ValueError:
                pass
        print(f"{pay_numbers=}")
        number_of_pay_items = len(pay_numbers) - 1

        pay_headers = []
        print("\n\n")

    def save_to_textfile(self, txtstr: str, filepath: Path) -> None:
        with open(filepath, "w") as writer:
            writer.write(txtstr)
        lg.info(f"saved to {filepath.name}")


class AmsPayslip(PdfObject):
    date: datetime.date
    actual_net_pay: Decimal
    accounting_pay: Decimal
    basic_pay: Decimal
    bonus_pay: Decimal
    aws_pay: Decimal
    deductable_cpf: Decimal
    deductable_cdc: Decimal
    deductable_pay: Decimal
    cpf_employee: Decimal
    cpf_employer: Decimal
    allowances_pckg: Decimal
    allowances_work: Decimal

    def __init__(
        self,
        filepath: Path,
        basic_pay: str = "",
        bonus_pay: str = "",
        aws_pay: str = "",
        deductable_pay: str = "",
        deductable_cpf: str = "",
        deductable_cdc: str = "",
        cpf_employee: str = "",
        cpf_employer: str = "",
        allowances_pckg: str = "",
        allowances_work: str = "",
    ):
        super().__init__(filepath)
        self.date = datetime.date(year=1, month=1, day=1)
        self.accounting_pay = Decimal("0.00")
        self.basic_pay = Decimal("0.00") if not basic_pay else Decimal(basic_pay)
        self.bonus_pay = Decimal("0.00") if not bonus_pay else Decimal(bonus_pay)
        self.aws_pay = Decimal("0.00") if not aws_pay else Decimal(aws_pay)
        self.deductable_cpf = (
            Decimal("0.00") if not deductable_cpf else Decimal(deductable_cpf)
        )
        self.deductable_cdc = (
            Decimal("0.00") if not deductable_cdc else Decimal(deductable_cdc)
        )
        self.deductable_pay = (
            Decimal("0.00") if not deductable_pay else Decimal(deductable_pay)
        )
        self.cpf_employee = (
            Decimal("0.00") if not cpf_employee else Decimal(cpf_employee)
        )
        self.cpf_employer = (
            Decimal("0.00") if not cpf_employer else Decimal(cpf_employer)
        )
        self.allowances_pckg = (
            Decimal("0.00") if not allowances_pckg else Decimal(allowances_pckg)
        )
        self.allowances_work = (
            Decimal("0.00") if not allowances_work else Decimal(allowances_work)
        )

    def __repr__(self) -> str:
        return f"""{self.__class__.__name__}(
        date={self.date}
        basic_pay={self.basic_pay}, accounting_pay={self.accounting_pay},
        bonus_pay={self.bonus_pay}, allowances_work={self.allowances_work},
        deductable_cpf={self.deductable_cpf}, deductable_cdc={self.deductable_cdc},
        deductable_pay={self.deductable_pay},
        cpf_employee={self.cpf_employee}, cpf_employer={self.cpf_employer},
        allowances_pckg={self.allowances_pckg},
        )"""

    @staticmethod
    def change_df_columns_descr_amt(df):
        cols = list(df.columns)
        cols[0] = "descr"
        cols[-1] = "amt"
        df.columns = cols
        return df

    def get_pay_date(self) -> datetime.date:
        df = super().get_paytable(area=AREA_DATE_BOX)
        df.set_index(df.columns[0], inplace=True)
        raw_date = df.loc["PERIOD", 1]
        if raw_date:
            res = str(raw_date).strip(":").strip()
            res = datetime.datetime.strptime(res, "%b-%Y")
            self.date = res
        return self.date

    def get_paytable(self) -> pd.DataFrame:
        df = super().get_paytable(area=AREA_PAYTABLE_BOX)
        df = self.change_df_columns_descr_amt(df)
        df.set_index(df.columns[0], inplace=True)
        data_entries = []
        column_current = "amt"
        try:
            kw = "BASIC PAY"
            basic_pay = df.loc[kw, column_current].replace(",", "")
            self.basic_pay = Decimal(basic_pay)
            data_entries.append(kw)
        except Exception as e:
            lg.warning(f"basic_pay parse error: {e=}")

        # PROSPERITY ANG BAO *
        try:
            for kw in [
                "PROSPERITY ANG BAO *",
                "URGENT TASK ALLOWANCE (A)",
                "TAXI CLAIM *",
            ]:
                try:
                    value = df.loc[kw, column_current].replace(",", "")
                except KeyError:
                    continue
                if value:
                    self.allowances_work += Decimal(value)
                    data_entries.append(kw)
        except Exception as e:
            lg.warning(f"allowances_pckg parse error: {e=}")

        try:
            for kw in [
                "MOBILE PHONE SUBSIDY",
                "EXECUTIVE HEALTH SCREENING",
                "HEALTH INSURANCE PREMIUM (SELF",
            ]:
                try:
                    value = df.loc[kw, column_current].replace(",", "")
                except KeyError:
                    continue
                if value:
                    self.allowances_pckg += Decimal(value)
                    data_entries.append(kw)
        except Exception as e:
            lg.warning(f"allowances_pckg parse error: {e=}")

        try:
            for kw in [
                "PROFIT SHARING",
                "RETENTION BONUS",
                "VARIABLE SALARY BONUS",
                "SEVERANCE PAY",
                "LEAVE ENCASHMENT",
                "ANNUAL WAGE SUPPLEMENT",
                "NOTICE IN LIEU_COMPANY",
                "LONG SERVICE AWARD - 3 YEARS",
            ]:
                try:
                    value = df.loc[kw, column_current].replace(",", "")
                except KeyError:
                    continue
                if value:
                    self.bonus_pay += Decimal(value)
                    data_entries.append(kw)
        except Exception as e:
            lg.warning(f"bonus_pay parse error: {e=}")

        lg.info(f"updated {data_entries=}")
        return df

    def get_deductions_table(self) -> pd.DataFrame:
        df = super().get_deductions_table(area=AREA_DEDUCTIONS_BOX)
        df = self.change_df_columns_descr_amt(df)
        df.set_index(df.columns[0], inplace=True)
        data_entries = []
        column_current = "amt"
        try:
            kw = "CHINESE DEVELOPMENT ASSISTANC"
            deductable_cdc = str(df.loc[kw, column_current])
            deductable_cdc = deductable_cdc.replace(",", "").replace("-", "")
            self.deductable_cdc = Decimal(deductable_cdc)
            data_entries.append(kw)
        except Exception as e:
            lg.warning(f"deductable_cdc parse error: {e=}")
        try:
            kw = "CPF CONTRIBUTION - EMPLOYEE"
            deductable_cpf = str(df.loc[kw, column_current])
            deductable_cpf = deductable_cpf.replace(",", "").replace("-", "")
            self.deductable_cpf = Decimal(deductable_cpf)
            data_entries.append(kw)
        except Exception as e:
            lg.warning(f"deductable_cpf parse error: {e=}")
        try:
            kw = "TOTAL DEDUCTIONS"
            deductable_pay = str(df.loc[kw, column_current])
            deductable_pay = deductable_pay.replace(",", "").replace("-", "")
            self.deductable_pay = Decimal(deductable_pay)
            data_entries.append(kw)
        except Exception as e:
            lg.warning(f"deductable_pay parse error: {e=}")
        lg.info(f"updated {data_entries=}")
        return df

    def get_pay_summary_table(self) -> pd.DataFrame:
        df = super().get_pay_summary_table(area=AREA_PAYSUMMARY_BOX)
        cols = list(df.columns)
        cols[0] = "descr"
        df.columns = cols
        df.set_index("descr", inplace=True)
        data_entries = []
        column_current = "CURRENT EARNING"
        try:
            kw = "Employee CPF"
            cpf_employee = str(df.loc[kw, column_current]).replace(",", "")
            self.cpf_employee = Decimal(cpf_employee)
            data_entries.append(kw)
        except Exception as e:
            lg.warning(f"cpf_employee parse error: {e=}")
        try:
            kw = "Employer CPF"
            cpf_employer = str(df.loc[kw, column_current]).replace(",", "")
            self.cpf_employer = Decimal(cpf_employer)
            data_entries.append(kw)
        except Exception as e:
            lg.warning(f"cpf_employer parse error: {e=}")
        lg.info(f"updated {data_entries=}")
        return df

    def crunch_data(self) -> pd.DataFrame:
        self.accounting_pay = (
            self.basic_pay
            + self.bonus_pay
            + self.allowances_pckg
            - self.deductable_cdc
            - self.deductable_cpf
        )

        self.actual_net_pay = self.accounting_pay + self.allowances_work

        df = pd.DataFrame(
            index=[self.date],
            data=[
                {
                    "accounting_pay": self.accounting_pay,
                    "actual_net_pay": self.actual_net_pay,
                    "basic_pay": self.basic_pay,
                    "bonus_pay": self.bonus_pay,
                    "aws_pay": self.aws_pay,
                    "deductable_cpf": self.deductable_cpf,
                    "deductable_cdc": self.deductable_cdc,
                    "deductable_pay": self.deductable_pay,
                    "cpf_employee": self.cpf_employee,
                    "cpf_employer": self.cpf_employer,
                    "allowances_pckg": self.allowances_pckg,
                    "allowances_work": self.allowances_work,
                }
            ],
        )
        return df


def load_environment():
    load_dotenv()
    global PASSWORD
    PASSWORD = os.getenv("PASSWORD")
    if not PASSWORD:
        raise MissingEnvVariables("PASSWORD")
    print(f"{PASSWORD=}")


def main():
    pathfinder = utils.PathFinder()

    dflist = []
    for i, payslip in enumerate(pathfinder.get_payslips()):
        ps = AmsPayslip(payslip)
        ps.get_pay_date()
        ps.get_paytable()
        ps.get_pay_summary_table()
        ps.get_deductions_table()
        dflist.append(ps.crunch_data())

    outname = "output.xlsx"
    df = pd.concat(dflist)
    print(df)
    # df.to_excel("output.xlsx")
    # lg.info(f"exported {outname}")


if __name__ == "__main__":
    main()
