import pymysql
import copy         # Copy data structures.
import pymysql.cursors
import json
from operator import itemgetter
import middleware.context as ctx

import logging
logger = logging.getLogger()

# Maximum number of data rows to display in the __str__().
_max_rows_to_print = ctx.get_context_value("MAX_TABLE_ROWS_TO_PRINT")

cursorClass = pymysql.cursors.DictCursor
charset = 'utf8mb4'


class RDBDataTable:


    def __init__(self, table_name, connect_info, key_columns=None):
        self._table_name = table_name
        self._db_name = connect_info["db"]
        self._key_columns = key_columns
        self._connect_info = copy.deepcopy(connect_info)
        self._cnx = pymysql.connect(host=connect_info['host'],
                              user=connect_info['user'],
                              password=connect_info['password'],
                              db=connect_info['db'],
                              charset=charset,
                              cursorclass=pymysql.cursors.DictCursor)

        self._table_file = self._db_name + "." + self._table_name


    def __str__(self):
        result = "Table name: {}, File name: {}, No of rows: {}, Key columns: {}"
        row_count = None
        columns = None
        key_names = None

        # Some of the values are not defined for a derived table. We will implement support for
        # derived tables later.
        if self._table_name:
            row_count = self.get_no_of_rows()
            columns = self.get_column_names()
            key_names = self.get_key_columns()
        else:
            row_count = "DERIVED"
            columns = "DERIVED"
            key_names = "DERIVED"

        if self._table_name is None:
            self._table_name = "DERIVED"

        result = result.format(self._table_name, self._table_name, row_count, key_names) + "\n"
        result += "Column names: " + str(columns)

        q_result = []
        if row_count != "DERIVED":
            if row_count <= _max_rows_to_print:
                q_result = self.find_by_template(None, fields=None, limit=None, offset=None)
            else:
                q_result = self.find_by_template(None, fields=None, limit=_max_rows_to_print)

            result += "\n First few rows: \n"
            for r in q_result:
                result += str(r) + "\n"

        return result

    def commit_rollback(self, cnx, kind="commit"):
        try:
            if kind == "commit":
                cnx.commit()
            elif kind == "rollback":
                cnx.rollback()
            else:
                pass
        except Exception as e:
            pass

    def run_q(self, q, args, cnx=None, cursor=None, commit=True, fetch=True):
        """
        :param q: The query string to run.
        :param fetch: True if this query produces a result and the function should perform and return fetchall()
        :return:
        """

        cursor_created = False
        cnx_created = False
        result = None

        try:
            if cnx is None:
                cnx = self._cnx
                cursor = self._cnx.cursor()
                cursor_created = True
            else:
                cnx = self._cnx
                cursor = cnx.cursor()
                cnx_created = True
                cursor_created = True

            log_message = cursor.mogrify(q, args)
            logger.debug(log_message)

            res = cursor.execute(q, args)

            if fetch:
                result = cursor.fetchall()
            else:
                result = res

            if commit:
                cnx.commit()
            if cursor_created:
                cursor.close()
            if cnx_created:
                cnx.close()
        except Exception as e:
            logger.warning("RDBDataTable.run_q, e = ", e)

            if commit:
                cnx.commit()
            if cursor_created:
                cursor.close()
            if cnx_created:
                cnx.close()

            raise e

        return result

    # Get the names of the columns
    def get_column_names(self):
        q = "show columns from " + self._table_name
        result = self.run_q(q, args=None, cnx=None, fetch=True)
        result = [r['Field'] for r in result]
        return list(result)

    def get_no_of_rows(self):
        q = "select count(*) as count from " + self._table_name
        result = self.run_q(q, args=None, cnx=None, fetch=True)
        result = result[0]['count']
        return result

    def get_key_columns(self):
        # This is MySQL specific and relies on the fact that MySQL returns the keys in
        # based on seq_in_index
        q = "show keys from " + self._table_name
        result = self.run_q(q, args=None, cnx=None, fetch=True)
        keys = [(r['Column_name'], r['Seq_in_index']) for r in result]
        keys = sorted(keys, key=itemgetter(1))
        keys = [k[0] for k in keys]
        return keys

    def get_primary_key_columns(self):
        # This is MySQL specific and relies on the fact that MySQL returns the keys in
        # based on seq_in_index
        q = "show keys from " + self._table_name + " WHERE Key_name = 'PRIMARY'"
        result = self.run_q(q, args=None, cnx=None, fetch=True)
        keys = [(r['Column_name'], r['Seq_in_index']) for r in result]
        keys = sorted(keys, key=itemgetter(1))
        keys = [k[0] for k in keys]
        return keys

    def template_to_where_clause(self, t):
        # Modify to return where clause template and args array.

        s = ""

        if t is None:
            return s

        for (k, v) in t.items():
            if s != "":
                s += " AND "
            s += k + "='" + v + "'"

        if s != "":
            s = "WHERE " + s

        return s

    def transfer_json_to_set_clause(self, t_json):

        args = []
        terms = []

        for k,v in t_json.items():
            args.append(v)
            terms.append(k + "=%s")

        clause = "set " + ", ".join(terms)

        return clause, args

    def find_by_template(self, t, fields=None, limit=None, offset=None):
        w = self.template_to_where_clause(t)
        if fields is None:
            fields = '*'
        else: # check if fields is missing key columns
            key_cols = self.get_primary_key_columns()
            for k in key_cols:
                if k not in fields:
                    fields += f", {k}"

        q = "SELECT " + fields + " FROM " + self._table_name + " " + w

        count_q = "SELECT COUNT(*) FROM " + self._table_name + " " + w
        count_run = self.run_q(count_q, args=None, fetch=True)
        total_count = count_run[0]['COUNT(*)']

        limit = limit if (limit is not None and int(limit) <= _max_rows_to_print) else _max_rows_to_print
        q += " limit " + str(limit)

        offset = offset if (offset is not None) else 0
        q += " offset " + str(offset)

        r = self.run_q(q, args=None, fetch=True)
        result = r
        # print("Query result = ", r)
        return result, total_count

    def find_by_primary_key(self, key, fields):
        key_columns = self.get_key_columns()
        tmp = dict(zip(key_columns, key))
        result = self.find_by_template(tmp, fields, None, None)
        return result

    def get_by_pattern(self, column, pattern):
        q = "select * from " + self._table_file + " where " + column\
            + " like '%" + pattern + "%';"
        result = self.run_q(q, args=None, fetch=True)
        return result


    def delete(self, template):

        # I did not call run_q() because it commits after each statement.
        # I run the second query to get row_count, then commit.
        # I should move some of this logic into run_q to handle getting
        # row count, running multiple statements, etc.
        where_clause = self.template_to_where_clause(template)
        q1 = "delete from " + self._table_file + " " + where_clause + ";"
        q2 = "select row_count() as no_of_rows_deleted;"
        cursor = self._cnx.cursor()
        cursor.execute(q1)
        cursor.execute(q2)
        result = cursor.fetchone()
        print(result)
        self._cnx.commit()
        return result

    def insert(self, row):
        keys = row.keys()
        q = "INSERT into " + self._table_file + " "
        s1 = list(keys)
        s1 = ",".join(s1)

        q += "(" + s1 + ") "

        vs = []
        for v in row.values():
            if isinstance(v, int):
                vs.append(v)
            else:
                vs.append("'"+v+"'")
        print("vs = ", vs)
        q += "values(" + ', '.join(list(map(str, vs))) + ")"
        print("Query: ", q)
        cnx = self._cnx
        cursor = cnx.cursor()
        res = cursor.execute(q)
        id = cnx.insert_id()
        cnx.commit()
        cnx.close()

        return id

    def update(self, template, row):
        set_clause, set_args  = self.transfer_json_to_set_clause(row)
        where_clause = self.template_to_where_clause(template)

        q = "UPDATE  " + self._table_file + " " + set_clause + " " + where_clause
        result = self.run_q(q, set_args, fetch=False)

        return result

    def get_count(self):
        return self.get_no_of_rows()