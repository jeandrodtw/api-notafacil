import pymysql

# O Django espera o driver "mysqlclient", que precisa ser compilado.
# O PyMySQL é Python puro e se passa por ele; a versão informada aqui
# é a mínima que o Django exige do mysqlclient.
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.install_as_MySQLdb()
