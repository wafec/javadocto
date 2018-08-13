package statemutest.util;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;

public class GenericHelper {
    GenericHelper() {}

    public static <T> T copyIfNotNull(T replace, T old) {
        if (replace != null) {
            return replace;
        }
        return old;
    }

    public static <T> List<T> mergeListsDistinct(List<T> a, List<T> b) {
        if (a == null && b == null)
            return new ArrayList<>();
        if (a == null)
            return new ArrayList<>(b);
        if (b == null)
            return new ArrayList<>(a);
        HashSet<T> hashSet = new HashSet<>();
        hashSet.addAll(a);
        hashSet.addAll(b);
        return new ArrayList<T>(hashSet);
    }
}
