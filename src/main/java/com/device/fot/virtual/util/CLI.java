package com.device.fot.virtual.util;

import java.util.Arrays;
import java.util.List;
import java.util.Optional;

/**
 *
 * @author Uellington Damasceno
 */
public class CLI {

    public static Optional<String> getDeviceId(String... args) {
        return getArgInList("-di", args);
    }

    public static Optional<String> getBrokerIp(String... args) {
        return getArgInList("-bi", args);
    }
    
    public static Optional<String> getPort(String... args){
        return getArgInList("-pt", args);
    }
    
    public static Optional<String> getPassword(String... args){
        return getArgInList("-pw", args);
    }
    
    public static Optional<String> getUsername(String... args){
        return getArgInList("-us", args);
    }
    
    public static Optional<String> getTimeout(String... args){
        return getArgInList("-to", args);
    }
    
    public static boolean hasParam(String arg, String... args){
        return Arrays.asList(args).indexOf(arg) != -1;
    }

    private static Optional<String> getArgInList(String arg, String... args) {
        List<String> largs = Arrays.asList(args);
        int index = largs.indexOf(arg);
        return (index == -1) ? Optional.empty() : Optional.of(largs.get(index + 1));
    }
}
