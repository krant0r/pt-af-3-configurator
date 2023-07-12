# python3.10
# af3_configurator.py
# конфигуратор для быстрого старта
#
__version__ = "0.1.1"

import sys
import argparse
#pip3 install ipcalc
import ipcalc

# pip3 install pandas
# pip3 install openpyxl
import pandas as pd

# выставим ширину вывода pandas-ы
pd.set_option('display.width', 300)
pd.set_option('display.max_columns', 50)

def main():
    # читаем параметры
    parser = argparse.ArgumentParser(prog="af3_configurator.py", prefix_chars="-", description="Конфигуратор конфигов для AF3", usage="af3_configurator.py -e ""AF3_configurator.xlsx"" -s ""Sheet1""")
    parser.add_argument("-e", "--excel", help="Excel file name", type=str, default="AF3_configurator.xlsx", required=False)
    parser.add_argument("-s", "--sheet", help="Excel Sheet name", type=str, default="Sheet1", required=False)
    args = parser.parse_args()

    # загружаем Excel-файл
    df = read_excel(args.excel, args.sheet)

    # заменить NaN на ""
    df = df.fillna("")
    # получить узлы
    get_af_nodes(df)

    cmd = []
    cmd += create_config(df)

    # распечатать команды
    with open("af3_configurator.sh", "w", encoding="utf-8", newline='\n') as txt_file:
        for line in cmd:
            txt_file.write(line + "\n")

    for x in cmd:
        print(x)

def create_config(df):
    clstr = []
    cmd = []
    hstn = []
    cmd_all = []

    cmd_all.append('wsc -ec "feature set custom_config_injection true"')
    cmd_all.append('wsc -ec "feature set waf_nginx_access_log true"')
    cmd_all += dns(df)
    cmd_all += ntp(df)

    cmd_all.append('wsc -c "password set ' + af_nodes[0].clstr_password + '"')

    # если кластер
    if len(af_nodes) > 1:
        for n in af_nodes:
            # собираем hostname
            cmd_all.append('wsc -c "host add ' + get_ip(n, "CLUSTER") + " " + n.hostname + '"')

    i = len(af_nodes)
    while i != 0:
        i -= 1
        if (af_nodes[i].hostname == ""):
            continue
            #break
        else:
            cmd.append('\n#\n# commands for ' + str(i+1) + ' node\n#')
            cmd += cmd_all
            cluster_ip = get_ip(af_nodes[i], "CLUSTER")
            if (cluster_ip == "None"):
                print("Ошибка, не определен интерфейс с ролью CLUSTER!")
                exit(1)
            gwint = df.iloc[22]['param']
            cmd += eth(ip_addr=af_nodes[i].eth0_ip, mask=af_nodes[i].eth0_netmask, gw=af_nodes[i].eth0_gw, role=af_nodes[i].eth0_role, ethN="eth-mgmt", mode=af_nodes[i].eth0_mode, gwint=gwint)
            cmd += eth(ip_addr=af_nodes[i].eth1_ip, mask=af_nodes[i].eth1_netmask, gw=af_nodes[i].eth1_gw, role=af_nodes[i].eth1_role, ethN="eth-cluster", mode=af_nodes[i].eth1_mode, gwint=gwint)
            cmd += eth(ip_addr=af_nodes[i].eth2_ip, mask=af_nodes[i].eth2_netmask, gw=af_nodes[i].eth2_gw, role=af_nodes[i].eth2_role, ethN="eth-ext1", mode=af_nodes[i].eth2_mode, gwint=gwint)
            cmd += eth(ip_addr=af_nodes[i].eth3_ip, mask=af_nodes[i].eth3_netmask, gw=af_nodes[i].eth3_gw, role=af_nodes[i].eth3_role, ethN="eth-int1", mode=af_nodes[i].eth3_mode, gwint=gwint)

            # если кластер
            if len(af_nodes) > 1:
                cmd.append('wsc -c "cluster set mongo local ' + af_nodes[i].hostname + '"')
                cmd.append('wsc -c "cluster set mongo replset waf"')
                if i == 0:
                    k = len(af_nodes)
                    ns = ""
                    while k != 1:
                        k -= 1
                        ns = ns + " " + af_nodes[k].hostname
                    cmd.append('wsc -c "cluster set mongo nodes ' + ns + '"')
                cmd.append('wsc -c "cluster set elastic replset waf"')
                k = 0
                ns = af_nodes[i].hostname
                while k != len(af_nodes) - 1:
                    k += 1
                    ns = ns + " " + af_nodes[(i-k)%(len(af_nodes))].hostname
                cmd.append('wsc -c "cluster set elastic nodes ' + ns + '"')
            cmd.append('wsc -c "config commit"')
    i = len(af_nodes)
    if i > 1:
        cmd.append('\n#\n# ожидаем пока соберется кластер монги и попросит выполнить config sync\n#')
    while i != 0:
        i -= 1
        if (af_nodes[i].hostname == ""):
            continue
            #break
        else:
            if len(af_nodes) != 1:
                cmd.append('\n#\n# commands for ' + str(i+1) + ' node\n#')
            cmd.append('wsc -c "config sync"')
    return(cmd)

def get_af_nodes(df):
    #
    # получаем данные по всем узлам
    #

    global af_nodes
    af_nodes = []
    for x in range(1, 7):
        if str(df.iloc[1]["node" + str(x)]) == "":
            continue
        af_nodes.append(AF_nodes(hostname=str(df.iloc[1]["node" + str(x)]),
                              clstr_password=str(df.iloc[0]["node" + str(x)]),
                              eth0_ip=str(df.iloc[2]["node" + str(x)]),
                              eth0_netmask=str(df.iloc[3]["node" + str(x)]),
                              eth0_gw=str(df.iloc[4]["node" + str(x)]),
                              eth0_role=str(df.iloc[5]["node" + str(x)]),
                              eth0_mode=str(df.iloc[6]["node" + str(x)]),
                              eth1_ip=str(df.iloc[7]["node" + str(x)]),
                              eth1_netmask=str(df.iloc[8]["node" + str(x)]),
                              eth1_gw=str(df.iloc[9]["node" + str(x)]),
                              eth1_role=str(df.iloc[10]["node" + str(x)]),
                              eth1_mode=str(df.iloc[11]["node" + str(x)]),
                              eth2_ip=str(df.iloc[12]["node" + str(x)]),
                              eth2_netmask=str(df.iloc[13]["node" + str(x)]),
                              eth2_gw=str(df.iloc[14]["node" + str(x)]),
                              eth2_role=str(df.iloc[15]["node" + str(x)]),
                              eth2_mode=str(df.iloc[16]["node" + str(x)]),
                              eth3_ip=str(df.iloc[17]["node" + str(x)]),
                              eth3_netmask=str(df.iloc[18]["node" + str(x)]),
                              eth3_gw=str(df.iloc[19]["node" + str(x)]),
                              eth3_role=str(df.iloc[20]["node" + str(x)]),
                              eth3_mode=str(df.iloc[21]["node" + str(x)])))

class AF_nodes:
    #
    # узел AF
    #
    def __init__(self, hostname, clstr_password, eth0_ip, eth0_netmask, eth0_gw, eth0_role, eth0_mode, eth1_ip, eth1_netmask, eth1_gw, eth1_role, eth1_mode, eth2_ip, eth2_netmask, eth2_gw, eth2_role, eth2_mode, eth3_ip, eth3_netmask, eth3_gw, eth3_role, eth3_mode):
        self.hostname = hostname
        self.clstr_password = clstr_password
        self.eth0_ip = eth0_ip
        self.eth0_netmask = eth0_netmask
        self.eth0_gw = eth0_gw
        self.eth0_role = eth0_role
        self.eth0_mode = eth0_mode
        self.eth1_ip = eth1_ip
        self.eth1_netmask = eth1_netmask
        self.eth1_gw = eth1_gw
        self.eth1_role = eth1_role
        self.eth1_mode = eth1_mode
        self.eth2_ip = eth2_ip
        self.eth2_netmask = eth2_netmask
        self.eth2_gw = eth2_gw
        self.eth2_role = eth2_role
        self.eth2_mode = eth2_mode
        self.eth3_ip = eth3_ip
        self.eth3_netmask = eth3_netmask
        self.eth3_gw = eth3_gw
        self.eth3_role = eth3_role
        self.eth3_mode = eth3_mode


def get_ip(node: AF_nodes, eth_role):
    #
    # получить IP-адрес интерфейса с указанной ролью
    #
    match eth_role:
        case node.eth0_role:
            return node.eth0_ip
        case node.eth1_role:
            return node.eth1_ip
        case node.eth2_role:
            return node.eth2_ip
        case node.eth3_role:
            return node.eth3_ip
        case _:
            return "None"

def eth(ip_addr,mask,gw,role,ethN,mode,gwint):
    #
    # настройка интерфейсов и маршрутов
    #

    cmd = []

    if (ip_addr != ""):
        if (mode == "static"):
            cmd.append('# настройка интерфейса ' + role)
            if(role == gwint):
                #commands.append('ip addr flush dev ' + ethN)
                #cmd.append('wsc -c "if set ' + ethN + ' role MGMT"')
                if (ip_addr != ""):
                    if (gw != ""):
                        cmd.append('wsc -c "dhcp set routers false"')
                    cmd.append('wsc -c "if set ' + ethN + ' inet_method static inet_address ' + ip_addr + " inet_netmask " + mask + " inet_gateway " + gw + " is_active true is_visible true" + '"')
            else:
                cmd.append('wsc -c "if set ' + ethN + ' inet_method static inet_address ' + ip_addr + " inet_netmask " + mask + " is_active true is_visible true" + '"')
                # если есть gw для LAN или CLUSTER
                if (gw != ""):
                    cmd.append('   # добавляем шлюз через отдельную таблицу для ' + role)
                    # номера таблиц должны отличаться, считаем, что у нас либо LAN, либо CLUSTER таблица
                    table_num = "128"
                    if (role == "LAN"):
                        table_num = "129"
                    elif (role == "CLUSTER"):
                        table_num = "130"
                    cmd.append('wsc -c "route table add ' + ethN + ' ' + table_num + '"')
                    cmd.append('wsc -c "route add default via ' + gw + ' dev '+ ethN + ' table ' + ethN + '"')
                    cmd.append('wsc -c "route rule add '+ ethN + ' from ' + ip_addr + '/32 table ' + ethN  + '"')
                    cmd.append('wsc -c "route rule add '+ ethN + ' to ' + ip_addr + '/32 table ' + ethN  + '"')
                    addr = ipcalc.IP(ip=str(ip_addr), mask=str(mask))
                    cmd.append('wsc -c "route add ' + str(addr.guess_network()) + ' dev '+ ethN + ' src ' + ip_addr + ' table ' + ethN  + '"')
        else:
            print("режим dhcp, но почему-то задан IP")
            # todo: что с dhcp?
            exit(1)
    else:
        if (mode == "dhcp"):
            if (role == "WAN"):
                cmd.append('wsc -c "if set ' + ethN + ' role WAN"')
            return(cmd)
    cmd.append('#')
    return(cmd)

def dns(df):
    #
    # DNS
    #
    cmd = []
    if (df.iloc[26]['node1'] != ""):
        cmd.append('wsc -c "dns add ' + df.iloc[26]['node1'] + '"')
        if (df.iloc[26]['node2'] != ""):
            cmd.append('wsc -c "dns add ' + df.iloc[26]['node2'] + '"')
            if (df.iloc[26]['node3'] != ""):
                cmd.append('wsc -c "dns add ' + df.iloc[26]['node3'] + '"')
    return(cmd)

def ntp(df):
    #
    # NTP
    #
    cmd = []
    if (df.iloc[24]['node1'] != ""):
        cmd.append('wsc -c "dhcp set ntp_servers false"')
        cmd.append('wsc -c "ntp add ' + df.iloc[24]['node1'] + '"')
        if (df.iloc[24]['node2'] != ""):
            cmd.append('wsc -c "ntp add ' + df.iloc[24]['node2'] + '"')
            if (df.iloc[24]['node3'] != ""):
                cmd.append('wsc -c "ntp add ' + df.iloc[24]['node3'] + '"')
    return(cmd)

def read_excel(excel_file, excel_sheet):
    #
    # Прочесть параметры AF3, и вернуть в виде таблицы
    #

    # открываем файл Excel, и загружаем лист из него
    data = pd.read_excel(excel_file, sheet_name=excel_sheet)
    df = pd.DataFrame(data, columns=['param', 'node1', 'node2', 'node3', 'node4', 'node5', 'node6'])
    print(df)
    return(df)

if __name__ == "__main__":
    # Вызов sys.exit() закрывает сессию интерпретатора
    # нужен import sys
    # sys.exit(main())
    main()