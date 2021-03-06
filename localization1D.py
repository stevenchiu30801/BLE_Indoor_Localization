### One dimension localization
# 1. Periodically read the log file
# 2. Plot the animated figure of RSSI samples
# 3. Compute estimated location of target
import sys
import re
import numpy as np
import statistics
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Beacon information
BEACON_NUM = 3
BEACON_POSITION = ((0, 0), (141, 0), (292, 0))
PATH_LOSS_VAR = ((-1.3048, -32.231), (-1.3303, -36.113), (-2.262, -15.512))    # (n, C), n: path loss exponent, C: environment constant
Rsqr = (0.8186, 0.5409, 0.8751)

#### RSSI Animation Variables #####
RSSI_ANIMATION = True
# Plot variables
PLOT_COLOR = ('tab:blue', 'tab:orange', 'tab:green', 'tab:red', 
              'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray', 
              'tab:olive', 'tab:cyan')

# Animation variables
RSSI_X_WINDOW = (0, 200)
RSSI_Y_WINDOW = (-80, -40)
RSSI_FPS = 5 # frames per second

##### Location Animation Variables #####
LOCATION_ANIMATION = not RSSI_ANIMATION
BCN_X = [BEACON_POSITION[i][0] for i in range(0, BEACON_NUM)]
BCN_Y = [BEACON_POSITION[i][1] for i in range(0, BEACON_NUM)]

# Plot variables
BCN_COLOR = 'tab:blue'  # beacons scatter color
TAR_COLOR = 'tab:red'   # target scatter color
BCN_AREA = np.pi * 5**2  # area
TAR_AREA = np.pi * 7**2

# Animation variables
LOC_X_WINDOW = (-200, 500)
LOC_Y_WINDOW = (-200, 500)
LOC_FPS = 5 # frames per second

##### Shared Variables #####
RSSI = [0 for i in range(0, BEACON_NUM)]
FILTER_FRAME = 5    # filter frame size

def rssi_init(lines):
    for l in lines:
        l.set_data([],[])
    return lines

def rssi_animate(i, file, lines):
    with open(file, 'r') as f:
        log = f.read().strip().split('\n')
    f.close()

    rssi = [[] for i in range(0, BEACON_NUM)]

    for i in range(0, len(log)):
        try:
            m = re.match('APP:INFO:', log[i])
            if m == None:
                continue
            data = log[i][m.end():].split(',')
            for j in range(0, BEACON_NUM):
                if int(data[0]) == j:
                    rssi[j].append(int(data[2]))
                    break
        except:
            pass

    for i in range(0, BEACON_NUM):
        ## Set global RSSI value
        ## Apply average filter
        if len(rssi[i]) - FILTER_FRAME <= 0:
            RSSI[i] = reduce(lambda x, y: x + y, rssi) / len(rssi[i])
        else:
            RSSI[i] = reduce(lambda x, y: x + y, rssi[i][len(rssi[i]) - FILTER_FRAME:]) / FILTER_FRAME

        if len(rssi[i]) - (RSSI_X_WINDOW[1] - RSSI_X_WINDOW[0]) <= 0:
            lines[i].set_data(np.arange(len(rssi[i])), rssi[i])
        else:
            lines[i].set_data(np.arange(RSSI_X_WINDOW[1] - RSSI_X_WINDOW[0]), rssi[i][len(rssi[i]) - (RSSI_X_WINDOW[1] - RSSI_X_WINDOW[0]):])

    return lines

def loc_init(scatters):
    scatters[0].set_offsets([[BCN_X[i], BCN_Y[i]] for i in range(0, BEACON_NUM)])
    scatters[1].set_offsets([[0, 0]])
    return scatters

def loc_animate(i, file, scatters):
    with open(file, 'r') as f:
        log = f.read().strip().split('\n')
    f.close()

    rssi = [[] for i in range(0, BEACON_NUM)]

    for i in range(0, len(log)):
        try:
            m = re.match('APP:INFO:', log[i])
            if m == None:
                continue
            data = log[i][m.end():].split(',')
            for j in range(0, BEACON_NUM):
                if int(data[0]) == j:
                    rssi[j].append(int(data[2]))
                    break
        except:
            pass

    for i in range(0, BEACON_NUM):
        # Set global RSSI value
        # Apply average filter
        RSSI[i] = rssi[i][len(rssi[i])-1]
      

    # print "RSSI: %.2f %.2f %.2f" % (RSSI[0], RSSI[1], RSSI[2])

    d = []
    for i in range(0, BEACON_NUM):
        d.append(10 ** ((RSSI[i] - PATH_LOSS_VAR[i][1]) / (10 * PATH_LOSS_VAR[i][0])))

    # print "distance: %.2f, %.2f, %.2f" % (d[0], d[1], d[2])

    ## Best fit line
    v = [[0, 0] for i in range(0, BEACON_NUM+1)]
    for i in range(0, BEACON_NUM):
        x = [(BCN_Y[(i+1)%BEACON_NUM]-BCN_Y[i])/(BCN_X[(i+1)%BEACON_NUM]-BCN_X[i])]
        y = [(BCN_X[(i+1)%BEACON_NUM]**2-BCN_X[i]**2+BCN_Y[(i+1)%BEACON_NUM]**2-BCN_Y[i]**2-d[(i+1)%BEACON_NUM]**2+d[i]**2)/(BCN_X[(i+1)%BEACON_NUM]-BCN_X[i])]

        A = np.vstack([x, np.ones(len(x))]).T

        v[i][1], v[i][0] = np.linalg.lstsq(A, y)[0]

    x = [(BCN_Y[(i+1)%BEACON_NUM]-BCN_Y[i])/(BCN_X[(i+1)%BEACON_NUM]-BCN_X[i]) for i in range(0, BEACON_NUM)]
    y = [(BCN_X[(i+1)%BEACON_NUM]**2-BCN_X[i]**2+BCN_Y[(i+1)%BEACON_NUM]**2-BCN_Y[i]**2-d[(i+1)%BEACON_NUM]**2+d[i]**2)/(BCN_X[(i+1)%BEACON_NUM]-BCN_X[i]) for i in range(0, BEACON_NUM)]

    A = np.vstack([x, np.ones(len(x))]).T

    v[BEACON_NUM][1], v[BEACON_NUM][0] = np.linalg.lstsq(A, y)[0]

    R = [(Rsqr[i]+Rsqr[(i+1)%BEACON_NUM])/(2*(Rsqr[0]+Rsqr[1]+Rsqr[2])) for i in range(0, BEACON_NUM)]
    X = v[0][0]*R[0] + v[1][0]*R[1] + v[2][0]*R[2]
    Y = v[0][1]*R[0] + v[1][1]*R[1] + v[2][1]*R[2]
    # print "Weight: (%d, %d)" % (X, Y)

    # print "Non-weight(2&0): (%d, %d)" % (v[2][0], v[2][1])
    # print "Pair all: (%d, %d)" % (v[3][0], v[3][1])

    ## ordered
    order = []
    if RSSI[0] > RSSI[1] and RSSI[0] > RSSI[2]:
        order.append((0, RSSI[0]))
        if RSSI[1] > RSSI[2]:
            order.append((1, RSSI[1]))
            order.append((2, RSSI[2]))
        else:
            order.append((2, RSSI[2]))
            order.append((1, RSSI[1]))
    elif RSSI[1] > RSSI[0] and RSSI[1] > RSSI[2]:
        order.append((1, RSSI[1]))
        if RSSI[0] > RSSI[2]:
            order.append((0, RSSI[0]))
            order.append((2, RSSI[2]))
        else:
            order.append((2, RSSI[2]))
            order.append((0, RSSI[0]))
    else:
        order.append((2, RSSI[2]))
        if RSSI[0] > RSSI[1]:
            order.append((0, RSSI[0]))
            order.append((1, RSSI[1]))
        else:
            order.append((1, RSSI[1]))
            order.append((0, RSSI[0]))

    # print order

    ## Heuristics
    if order[0][1] > -50:
        x = BCN_X[order[0][0]]
    else:
        if order[0][1] - order[1][1] < 8:
            # x = (BCN_X[order[0][0]] + BCN_X[order[1][0]]) / 2
            if order[0][0] > order[1][0]:
                x = (BCN_X[order[0][0]] - d[order[0][0]] + BCN_X[order[1][0]] + d[order[1][0]]) / 2
            else:
                x = (BCN_X[order[0][0]] + d[order[0][0]] + BCN_X[order[1][0]] - d[order[1][0]]) / 2
        elif order[0][0] == 0:
            x = BCN_X[0] - d[order[0][0]]
        elif order[0][0] == 2:
            x = BCN_X[2] + d[order[0][0]]
        else:
            return scatters

    print "distance: %d" % x

    # with open("eval_1212.txt", 'a') as f:
    #     f.write("%d\n" % x)
    #     f.close()

    # scatters[1].set_offsets([v[0][0], v[0][1]])
    # scatters[2].set_offsets([v[1][0], v[1][1]])
    # scatters[3].set_offsets([v[2][0], v[2][1]])
    # scatters[4].set_offsets([v[3][0], v[3][1]])
    # scatters[5].set_offsets([X, Y])
    scatters[1].set_offsets([x, 0])
    # except:
        # pass

    return scatters

def main():
    if len(sys.argv) != 2:
        print "Usage: python %s <log_file>" % sys.argv[0]
        exit(1)

    file = sys.argv[1]

    ##### RSSI Animation #####
    if RSSI_ANIMATION:
        fig = plt.figure()
        ax = plt.axes(xlim=(RSSI_X_WINDOW[0], RSSI_X_WINDOW[1]), 
                      ylim=(RSSI_Y_WINDOW[0], RSSI_Y_WINDOW[1]))

        plt.xlabel("Samples")
        plt.ylabel("RSSI")

        lines = []
        for i in range(0, BEACON_NUM):
            lines.append(ax.plot([], [], color=PLOT_COLOR[i], label="Beacon %d" % i)[0])
      
        ani = animation.FuncAnimation(fig, rssi_animate, frames=None, init_func=lambda: rssi_init(lines), fargs=(file, lines), interval=1000/RSSI_FPS, blit=True)

        plt.title("RSSI Value")
        plt.legend()
        plt.show()

    ##### Localization Animation #####
    if LOCATION_ANIMATION:
        fig = plt.figure()
        ax = plt.axes(xlim=(LOC_X_WINDOW[0], LOC_X_WINDOW[1]), 
                      ylim=(LOC_Y_WINDOW[0], LOC_Y_WINDOW[1]))

        plt.xlabel("X (meter)")
        plt.ylabel("Y (meter)")

        scatters = []    # one for beacons, the other for target
        scatters.append(ax.scatter([], [], s=BCN_AREA, c=BCN_COLOR, alpha=0.8, label="Beacon"))
        # scatters.append(ax.scatter([], [], s=TAR_AREA, c='tab:orange', alpha=0.8, label="Pair 01"))
        # scatters.append(ax.scatter([], [], s=TAR_AREA, c='tab:green', alpha=0.8, label="Pair 12"))
        # scatters.append(ax.scatter([], [], s=TAR_AREA, c='tab:purple', alpha=0.8, label="Pair 20"))
        # scatters.append(ax.scatter([], [], s=TAR_AREA, c='tab:cyan', alpha=0.8, label="Pair 012"))
        # scatters.append(ax.scatter([], [], s=TAR_AREA, c=TAR_COLOR, alpha=0.8, label="Weighted"))
        scatters.append(ax.scatter([], [], s=TAR_AREA, c='tab:olive', alpha=0.8, label="ordered"))


        ani = animation.FuncAnimation(fig, loc_animate, frames=None, init_func=lambda: loc_init(scatters), fargs=(file, scatters,), interval=1000/RSSI_FPS, blit=True)
        plt.title("Location")
        plt.legend()
        plt.show()

if __name__ == "__main__":
    main()