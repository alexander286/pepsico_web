import os
import oracledb

# 👇 Ajusta estos datos
os.environ['TNS_ADMIN'] = r'C:\Users\bnlok\Downloads\Wallet_PEPSICOAPT'   # Ruta donde está tu wallet
user = "ADMIN"                                      # O APP_APT si prefieres
pwd  = "Abcdefg123456789*"

aliases = [
    "pepsicoapt_high",
    "pepsicoapt_medium",
    "pepsicoapt_low",
    "pepsicoapt_tp",
    "pepsicoapt_tpurgent"
]

for a in aliases:
    print(f"Probando alias: {a}")
    try:
        conn = oracledb.connect(user=user, password=pwd, dsn=a)
        with conn.cursor() as c:
            c.execute("select 'OK' from dual")
            print("✅ Conexión exitosa ->", a, c.fetchone())
        conn.close()
    except Exception as e:
        print("❌ Error con alias:", a, "-", e)
    print("-" * 50)
